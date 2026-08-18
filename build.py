#!/usr/bin/env python3
"""
Build the DQ6 Script Refill ROM from a stock NoPrgress ROM.

This is the script that produced the released patch. It is published so the
build is reproducible and so anyone can see exactly what is written where.

  usage:  build.py <noprgress.sfc> <candidates-en.txt> <crashfix-v2.ips> <out.sfc>

It does four things:
  1. applies the v2 crash-fix IPS (Info > All, and Forget)
  2. decodes all 6,960 messages from the unmodified payload
  3. substitutes the 421 authored English messages
  4. re-encodes every message with the ROM'S EXISTING Huffman trees, rebuilds
     the 870-entry pointer table, and recomputes the internal checksum

The trees are never modified. Every symbol already has exactly one code path in
them, so the encode is deterministic and the 6,539 messages that are not
touched come out byte-identical to the ones NoPrgress shipped. That property is
worth checking after any change to this script: decode the output and compare
the untouched messages against the input.

Message system, decoded from the ROM at $C0:2B69 onward:
  - Pointer table at $C1:5BB5, 870 entries of 3 bytes, indexed by (ID >> 3).
    Each entry heads a run of 8 messages, so the ID space is 6,960.
  - entry >> 3 is a byte offset from $F7:175B; entry & 7 is the start bit.
  - Huffman trees at $C1:67BE (bit clear) and $C1:700E (bit set); nodes are
    byte-indexed 16-bit words, MSB-first, bit 15 set = internal node.
  - The tree root is read from the code at $C0:2BFB and differs per ROM.
  - Messages end on $00AC or $00AE and each message keeps its own terminator.

Standard library only. Writes one file, the output ROM.
"""
import io, re, sys, hashlib, zlib

TBL, PAY = 0x015BB5, 0x370000 + 0x175B
T0, T1 = 0x0167BE, 0x01700E
TERM = (0x00AC, 0x00AE)
NAMETBL = 0x011100
GROUPS = 870
HDR = 0x00FFC0
FREE_END = 0x3B874B      # measured: no reads observed in $FB:2133-$FB:874B


class Rom:
    def __init__(self, data):
        self.d = data
        assert self.d[0x2bfa] == 0xA2, 'not a DQ6 ROM: no LDX #imm at $C0:2BFA'
        self.root = self.d[0x2bfb] | (self.d[0x2bfc] << 8)

    def sym(self, b):
        o = NAMETBL + b * 2
        return self.d[o] | (self.d[o + 1] << 8)

    def entry(self, g):
        o = TBL + g * 3
        return self.d[o] | (self.d[o + 1] << 8) | (self.d[o + 2] << 16)

    def decode_all(self):
        """Every message as (symbols, terminator), in ID order."""
        d, out = self.d, []
        for g in range(GROUPS):
            e = self.entry(g)
            A = (e >> 3) * 8 + (7 - (e & 7))
            for _ in range(8):
                syms = []
                while True:
                    x = self.root
                    while True:
                        b = (d[PAY + (A >> 3)] >> (7 - (A & 7))) & 1
                        A += 1
                        base = T1 if b else T0
                        v = d[base + x] | (d[base + x + 1] << 8)
                        if v & 0x8000:
                            x = v & 0x7FFF
                        else:
                            break
                    if v in TERM:
                        break
                    syms.append(v)
                out.append((syms, v))
        return out

    def codes(self):
        """symbol -> bit string, by walking both trees from the root."""
        d, out, stack = self.d, {}, [(self.root, '', frozenset([self.root]))]
        while stack:
            x, pre, seen = stack.pop()
            if len(pre) > 64:
                continue
            for b in (0, 1):
                base = T1 if b else T0
                v = d[base + x] | (d[base + x + 1] << 8)
                if v & 0x8000:
                    nx = v & 0x7FFF
                    if nx not in seen:
                        stack.append((nx, pre + str(b), seen | {nx}))
                elif v not in out:
                    out[v] = pre + str(b)
        return out


class BitWriter:
    def __init__(self):
        self.by, self.n = bytearray(), 0

    def put(self, bits):
        for c in bits:
            if self.n % 8 == 0:
                self.by.append(0)
            if c == '1':
                self.by[-1] |= 1 << (7 - (self.n % 8))
            self.n += 1


def apply_ips(rom, ips):
    assert ips[:5] == b'PATCH', 'not an IPS file'
    i, n = 5, 0
    while ips[i:i + 3] != b'EOF':
        off = int.from_bytes(ips[i:i + 3], 'big'); i += 3
        ln = int.from_bytes(ips[i:i + 2], 'big'); i += 2
        if ln:
            rom[off:off + ln] = ips[i:i + ln]; i += ln
        else:
            rl = int.from_bytes(ips[i:i + 2], 'big'); i += 2
            rom[off:off + rl] = bytes([ips[i]]) * rl; i += 1
        n += 1
    return n


REC = re.compile(r'^---- (\d+)$')
TOKEN = re.compile(r'\{([0-9A-Z]{2,4})\}')
# notation used in the candidates file for two symbols with no ASCII equivalent
NOTATION = {'SPK': 0x240, 'STAR': 0x559}


def read_candidates(path):
    """Parse candidates-en.txt back into {id: text}.

    The emitted format uses fixed-width prefixes so this is exactly reversible,
    including leading spaces inside a message, which at least one message
    deliberately has. Do not strip() here: that silently ate an indent the
    first time this was written.
        "  "        starts a message body
        "     | "   a page break, then the rest of the line
        "     / "   a line break, then the rest of the line
    """
    out, cur, buf = {}, None, []

    def flush():
        if cur is not None:
            out[cur] = ''.join(buf)

    for raw in io.open(path, encoding='utf-8'):
        line = raw.rstrip('\r\n')
        m = REC.match(line.strip())
        if m:
            flush()
            cur, buf = int(m.group(1)), []
            continue
        if cur is None:
            continue
        if line.startswith('  -- '):          # a note, not content
            continue
        if not line.strip():                  # blank line ends the record
            flush()
            cur, buf = None, []
            continue
        if line.startswith('     | '):
            buf.append('{AF}' + line[7:])
        elif line.startswith('     / '):
            buf.append('{AD}' + line[7:])
        elif line.rstrip() == '     |':
            buf.append('{AF}')
        elif line.rstrip() == '     /':
            buf.append('{AD}')
        elif line.startswith('  '):
            buf.append(line[2:])
    flush()
    return out


def main(src, cand, ips_path, dst):
    rom = bytearray(io.open(src, 'rb').read())
    src_crc = zlib.crc32(bytes(rom)) & 0xFFFFFFFF
    print('source ROM: %d bytes, CRC32 %08X' % (len(rom), src_crc))

    n = apply_ips(rom, io.open(ips_path, 'rb').read())
    print('crash-fix IPS applied: %d records' % n)

    r = Rom(bytes(io.open(src, 'rb').read()))
    msgs = r.decode_all()
    codes = r.codes()
    print('decoded %d messages; %d symbols are encodable in this ROM' % (len(msgs), len(codes)))

    inv = {}
    for i, b in enumerate(range(0x02, 0x0C)):
        inv.setdefault('0123456789'[i], r.sym(b))
    for i, b in enumerate(range(0x10, 0x2A)):
        inv.setdefault('ABCDEFGHIJKLMNOPQRSTUVWXYZ'[i], r.sym(b))
    for i, b in enumerate(range(0x42, 0x5C)):
        inv.setdefault('abcdefghijklmnopqrstuvwxyz'[i], r.sym(b))
    inv.setdefault("'", r.sym(0x77))
    inv[' '] = 0x200
    for ch, s in (('.', 0x242), (',', 0x243), ('!', 0x246), ('?', 0x228),
                  ('*', 0x247), ('-', 0x236)):
        inv[ch] = s
    # The font carries a single glyph for "'s". NoPrgress use it throughout, so
    # matching it greedily is what keeps the encode identical to theirs and
    # costs a few hundred bytes less than spelling it out.
    LIGATURE = ("'s", 0x24D)

    def encode(t, mid):
        out, k = [], 0
        while k < len(t):
            m = TOKEN.match(t, k)
            if m:
                nm = m.group(1)
                out.append(NOTATION[nm] if nm in NOTATION else int(nm, 16))
                k = m.end(); continue
            if t[k:k + len(LIGATURE[0])] == LIGATURE[0]:
                out.append(LIGATURE[1]); k += len(LIGATURE[0]); continue
            ch = t[k]
            if ch not in inv:
                raise SystemExit('message %d: cannot encode %r' % (mid, ch))
            out.append(inv[ch]); k += 1
        return out

    C = read_candidates(cand)
    for mid, text in C.items():
        msgs[mid] = (encode(text, mid), msgs[mid][1])
    print('messages substituted: %d' % len(C))

    w = BitWriter()
    starts = []
    for g in range(GROUPS):
        starts.append(w.n)
        for k in range(8):
            syms, term = msgs[g * 8 + k]
            for s in syms:
                w.put(codes[s])
            w.put(codes[term])
    payload = bytes(w.by)
    end = PAY + len(payload)
    print('payload: %d bytes, ends at 0x%06X, headroom %d bytes'
          % (len(payload), end, FREE_END - end))
    if end >= FREE_END:
        raise SystemExit('payload overruns the free region')

    rom[PAY:PAY + len(payload)] = payload
    for g in range(GROUPS):
        A = starts[g]
        e = ((A // 8) << 3) | (7 - (A % 8))
        o = TBL + g * 3
        rom[o], rom[o + 1], rom[o + 2] = e & 0xFF, (e >> 8) & 0xFF, (e >> 16) & 0xFF

    rom[HDR + 0x1C:HDR + 0x1E] = b'\xFF\xFF'
    rom[HDR + 0x1E:HDR + 0x20] = b'\x00\x00'
    ck = sum(rom) & 0xFFFF
    rom[HDR + 0x1C:HDR + 0x1E] = bytes([(ck ^ 0xFFFF) & 0xFF, ((ck ^ 0xFFFF) >> 8) & 0xFF])
    rom[HDR + 0x1E:HDR + 0x20] = bytes([ck & 0xFF, (ck >> 8) & 0xFF])

    out = bytes(rom)
    io.open(dst, 'wb').write(out)
    print()
    print('wrote %s' % dst)
    print('  size  %d bytes' % len(out))
    print('  CRC32 %08X' % (zlib.crc32(out) & 0xFFFFFFFF))
    print('  SHA-1 %s' % hashlib.sha1(out).hexdigest())


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(__doc__.strip().split('\n\n')[1])
        sys.exit(2)
    main(*sys.argv[1:])
