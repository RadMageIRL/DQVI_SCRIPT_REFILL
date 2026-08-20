#!/usr/bin/env python3
"""Check a patched DQ6 ROM against the one it was built from.

  usage:  verify.py <stock NoPrgress.sfc> <patched.sfc>

You supply both ROMs. Nothing else is needed and nothing is written.

This is the verification the README claims, run against two files rather than
quoted. It checks six things:

  1. not one word of NoPrgress's own writing is altered. Their messages are
     allowed to differ in exactly one way, the redundant opening marker being
     dropped, and the check fails if any other symbol in any of them moves
  2. no message still displays its own ID
  3. every one of the 2,512 name-table string IDs resolves the way the game
     resolves it, in both ROMs, and the two are compared
  4. both crash fixes are present at every site they touch
  5. the gold window's draw call and descriptor are in place
  6. the header still says what it said, and the internal checksum agrees

Point 3 is the one that matters most and the one a byte diff cannot do. The
name table is repacked wholesale, so almost every byte in it moves; comparing
bytes tells you nothing at all. Resolving IDs tells you what changed on screen.

Standard-library Python 3 only. No dependencies, nothing to install.
"""
import io
import os
import sys
import zlib

# --- the message script -----------------------------------------------------
ROOT_AT = 0x002BFB
TREE0, TREE1 = 0x0167BE, 0x01700E
TABLE = 0x015BB5
PAYLOAD = 0x37175B
BYTETBL = 0x011100
GROUPS, PER_GROUP = 870, 8
TERMINATORS = (0x00AC, 0x00AE)
GLYPH = 0x0200

# --- the name table ---------------------------------------------------------
NT_PTR = 0x0165E7
NT_BASE = 0x3B8703
NT_END = 0x3BC712
NT_GROUPS = 157
NT_TERM = 0xAC

# --- the two crash fixes ----------------------------------------------------
CF_SPAN = 0x033538
CF_AFTER = bytes.fromhex(
    "8dc23a22257bc3a9870022fe83c3a9260022fe83c3a92c0022fe83c322f975c3"
    "a92d0022fe83c322f975c3a92e0022fe83c322f975c3a92f0022fe83c322f975"
    "c3a9300022fe83c3a98a0022fe83c3abc2307afa68286b")
CF_WIDTH, CF_LENGTH, CF_BUFFER = 0x55BE, 0x55C0, 0x55C2
CF_RELOCATIONS = (
    (0x00FDD5, CF_LENGTH), (0x00FDE0, CF_LENGTH), (0x00FDE8, CF_LENGTH),
    (0x00FDFE, CF_LENGTH), (0x00FE24, CF_LENGTH), (0x00FF03, CF_LENGTH),
    (0x00FF1A, CF_LENGTH), (0x00FF1F, CF_LENGTH), (0x00FDE3, CF_BUFFER),
    (0x00FE29, CF_BUFFER), (0x00FE69, CF_BUFFER), (0x00FEF2, CF_BUFFER),
    (0x00FF22, CF_BUFFER), (0x00FF34, CF_BUFFER), (0x00FE81, CF_WIDTH),
    (0x00FE85, CF_WIDTH), (0x00FE8B, CF_WIDTH), (0x00FEA2, CF_WIDTH),
    (0x00FEA7, CF_WIDTH))
CF_BRANCHES = ((0x00FE27, 0xB0), (0x00FF1D, 0x90))

# --- the gold window --------------------------------------------------------
GOLD_CODE_AT = 0x033593
GOLD_CODE_NOW = bytes.fromhex('A91000223A76C3A93E0022FE83C3ABC2307AFA68286B')
GOLD_DESC_AT = 0x057E88
GOLD_DESC_NOW = bytes([0x01, 0x01, 0x09])

HDR = 0x00FFC0

# The redundant opening marker on untagged NPC lines. The engine already draws
# a marker there; $0559 sat after it, is the one symbol in their script with no
# English glyph behind it, and is dropped.
MARKER = 0x0559


class Fail(Exception):
    pass


class Rom(object):
    def __init__(self, path):
        self.path = path
        self.d = io.open(path, 'rb').read()
        if len(self.d) < NT_END:
            raise Fail('%s is too small to be a DQ6 ROM (%d bytes).'
                       % (os.path.basename(path), len(self.d)))
        if self.d[ROOT_AT - 1] != 0xA2:
            raise Fail('no LDX #imm at $C0:2BFA in %s.\n  This does not look '
                       'like a DQ6 ROM.' % os.path.basename(path))
        self.root = self.d[ROOT_AT] | (self.d[ROOT_AT + 1] << 8)

    def crc(self):
        return zlib.crc32(self.d) & 0xFFFFFFFF

    def sha1(self):
        import hashlib
        return hashlib.sha1(self.d).hexdigest()

    def messages(self):
        d, out = self.d, []
        for g in range(GROUPS):
            o = TABLE + g * 3
            e = d[o] | (d[o + 1] << 8) | (d[o + 2] << 16)
            bit = (e >> 3) * 8 + (7 - (e & 7))
            for _ in range(PER_GROUP):
                syms = []
                while True:
                    node = self.root
                    while True:
                        b = (d[PAYLOAD + (bit >> 3)] >> (7 - (bit & 7))) & 1
                        bit += 1
                        base = TREE1 if b else TREE0
                        v = d[base + node] | (d[base + node + 1] << 8)
                        if v & 0x8000:
                            node = v & 0x7FFF
                        else:
                            break
                    if v in TERMINATORS:
                        break
                    syms.append(v)
                out.append((tuple(syms), v))
        return out

    def digits(self):
        """symbol -> digit character, from the ROM's own byte table."""
        out = {}
        for i in range(10):
            o = BYTETBL + (0x02 + i) * 2
            out[self.d[o] | (self.d[o + 1] << 8)] = chr(48 + i)
        return out

    def names(self):
        """string ID -> raw entry bytes, resolved the way $C0:315E does."""
        entries, start = [], NT_BASE
        for i in range(NT_BASE, NT_END):
            if self.d[i] == NT_TERM:
                entries.append(self.d[start:i])
                start = i + 1
        index_at, addr = {}, NT_BASE
        for n, e in enumerate(entries):
            index_at[addr] = n
            addr += len(e) + 1
        out = {}
        for g in range(NT_GROUPS):
            o = NT_PTR + g * 3
            raw = self.d[o] | self.d[o + 1] << 8 | self.d[o + 2] << 16
            a = (0xFB8703 + raw) & 0xFFFFFF
            key = ((a >> 16) & 0x3F) << 16 | (a & 0xFFFF)
            if key not in index_at:
                raise Fail('%s: name-table group %d does not line up with the '
                           'strings.' % (os.path.basename(self.path), g))
            base = index_at[key]
            for low in range(16):
                out[g * 16 + low] = entries[base + low]
        return out


def line(ok, text, detail=''):
    print('  [%s] %s%s' % ('PASS' if ok else 'FAIL', text,
                           ('   %s' % detail) if detail else ''))
    return 0 if ok else 1


def main(argv):
    if not argv or argv[0] in ('-h', '--help') or len(argv) != 2:
        print(__doc__.strip())
        return 0 if argv and argv[0] in ('-h', '--help') else 2

    base, built = Rom(argv[0]), Rom(argv[1])
    print('build verification')
    print('=' * 78)
    print('  source   %s' % os.path.basename(base.path))
    print('           %13s bytes   CRC32 %08X'
          % ('{:,}'.format(len(base.d)), base.crc()))
    print('  built    %s' % os.path.basename(built.path))
    print('           %13s bytes   CRC32 %08X'
          % ('{:,}'.format(len(built.d)), built.crc()))
    print('           SHA-1 %s' % built.sha1())
    print()

    if base.crc() == built.crc():
        raise Fail('those are the same ROM. Give the stock one first and the '
                   'patched one second.')

    bad = 0

    # 1 and 2 --------------------------------------------------------------
    old, new = base.messages(), built.messages()
    if len(old) != len(new):
        raise Fail('the two ROMs decode to different message counts.')
    dig = base.digits()

    def shows_own_id(msgs, i):
        text = ''.join(dig.get(s, '\x00') for s in msgs[i][0] if s >= GLYPH)
        return text.lstrip('\x00').startswith(str(i)) and i >= 10

    was_placeholder = set(i for i in range(len(old)) if shows_own_id(old, i))
    changed = set(i for i in range(len(old)) if old[i] != new[i])
    theirs = [i for i in range(len(old)) if i not in was_placeholder]
    touched = [i for i in theirs if old[i] != new[i]]

    # Their messages may differ in exactly one way and no other: the opening
    # speech marker $0559, which has no English glyph, swapped for the plain
    # asterisk $0247 they already use. Anything else is a word changed.
    marker, reworded = [], []
    for i in touched:
        o, n = old[i][0], new[i][0]
        if o and o[0] == MARKER and o[1:] == n:
            marker.append(i)
        else:
            reworded.append(i)
    bad += line(not reworded,
                'not one word of their %d messages is altered' % len(theirs),
                'reworded: %d' % len(reworded))
    bad += line(True,
                'the redundant opening marker dropped, and nothing else',
                '%d messages, symbol $%04X removed' % (len(marker), MARKER))
    still = [i for i in range(len(new)) if shows_own_id(new, i)]
    bad += line(not still,
                'no message still displays its own ID',
                'remaining: %d' % len(still))
    bad += line(changed >= was_placeholder,
                'all %d unwritten messages were written'
                % len(was_placeholder),
                'left alone: %d' % len(was_placeholder - changed))
    terms = [i for i in range(len(old)) if old[i][1] != new[i][1]]
    bad += line(not terms, 'every message terminator preserved',
                'differing: %d' % len(terms))
    print()

    # 3 --------------------------------------------------------------------
    on, nn = base.names(), built.names()
    ids = sorted(on)
    diff = [i for i in ids if on[i] != nn[i]]
    same = len(ids) - len(diff)
    bad += line(True, 'name table resolved by string ID in both ROMs',
                '%d IDs' % len(ids))
    print('       %d changed, %d untouched' % (len(diff), same))
    print('       (the table is repacked wholesale, so this is the only')
    print('       comparison that means anything. A byte diff would show')
    print('       almost the whole region as different and prove nothing.)')
    print()

    # 4 --------------------------------------------------------------------
    span = built.d[CF_SPAN:CF_SPAN + len(CF_AFTER)] == CF_AFTER
    bad += line(span, 'Info > All: the 87-byte span is restored',
                '0x%06X' % CF_SPAN)
    sites = sum(1 for off, want in CF_RELOCATIONS
                if (built.d[off + 1] | built.d[off + 2] << 8) == want)
    branches = sum(1 for off, want in CF_BRANCHES if built.d[off] == want)
    bad += line(sites == len(CF_RELOCATIONS) and branches == len(CF_BRANCHES),
                'Forget: word-wrap state relocated',
                '%d/%d operands, %d/%d branches'
                % (sites, len(CF_RELOCATIONS), branches, len(CF_BRANCHES)))
    print()

    # 5 --------------------------------------------------------------------
    code = built.d[GOLD_CODE_AT:GOLD_CODE_AT + len(GOLD_CODE_NOW)]
    bad += line(code == GOLD_CODE_NOW, 'gold window: the draw call is back',
                '0x%06X' % GOLD_CODE_AT)
    desc = built.d[GOLD_DESC_AT:GOLD_DESC_AT + len(GOLD_DESC_NOW)]
    bad += line(desc == GOLD_DESC_NOW, 'gold window: descriptor 58 moved',
                'x=%d y=%d w=%d' % tuple(desc))
    win_lo, win_hi = 0x057B5C, 0x057B5C + 14 * 128
    moved = [i for i in range(win_lo, win_hi)
             if base.d[i] != built.d[i] and not
             GOLD_DESC_AT <= i < GOLD_DESC_AT + 14]
    bad += line(not moved, 'no other window descriptor changed',
                '%d bytes differ elsewhere in the table' % len(moved))
    print()

    # 6 --------------------------------------------------------------------
    bad += line(base.d[HDR + 0x15:HDR + 0x18] == built.d[HDR + 0x15:HDR + 0x18],
                'header mapmode and ROM size unchanged')
    ck = int.from_bytes(built.d[HDR + 0x1E:HDR + 0x20], 'little')
    cx = int.from_bytes(built.d[HDR + 0x1C:HDR + 0x1E], 'little')
    total = sum(built.d) & 0xFFFF
    bad += line((ck ^ cx) == 0xFFFF and ck == total,
                'internal checksum consistent',
                '%04X, complement %04X, recomputed %04X' % (ck, cx, total))
    print()

    if bad:
        print('  %d check%s failed.' % (bad, '' if bad == 1 else 's'))
        print()
        return 1
    print('  Everything checked here passes. That is not the same as')
    print('  "the game is correct": these are structural checks, and text')
    print('  that is correctly inserted can still read badly or overrun a')
    print('  window. Play it.')
    print()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Fail as exc:
        print('\nERROR: %s\n' % exc, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as exc:
        print('\nERROR: cannot open %s\n' % exc.filename, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
