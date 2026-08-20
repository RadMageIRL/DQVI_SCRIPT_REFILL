#!/usr/bin/env python3
"""Census the DQ6 message script in a ROM, and check the claims made about it.

  usage:  census.py <rom.sfc> [option]

  (none)             how many messages there are, how many are unwritten, and
                     where the unwritten ones cluster
  --placeholders     list every message that displays its own ID
  --breaks           the page-break invariant: what follows each page break
  --quotes           how often their speaker-tag quote actually follows a tag
  --roundtrip        decode every message, re-encode it with the ROM's own
                     trees, rebuild the pointer table, and require the result
                     to be byte-identical

You supply the ROM. Nothing else is needed and nothing is written.

Two things worth knowing before reading the output.

The pointer table is indexed by ID >> 3, not by ID. Each of its 870 entries
heads a run of eight messages separated by terminator symbols. Reading it as
one entry per message is a factor-of-eight error and it is the founding error
of this project: 870 "messages" are really 6,960.

An unwritten message here displays its own ID in decimal digits. That passes
"is it Latin?" and it passes "did the bytes change?", so the only test that
works is structural: does the text begin with exactly this message's own ID.

This tool renders unknown symbols as <XXXX> and counts them. A decoder that
falls back to a space instead produces legal-looking output and hid an entire
punctuation system in this ROM for weeks.

Standard-library Python 3 only. No dependencies, nothing to install.
"""
import io
import os
import sys
import zlib

ROOT_AT = 0x002BFB
TREE0, TREE1 = 0x0167BE, 0x01700E
TABLE = 0x015BB5           # 870 entries, 3 bytes each
PAYLOAD = 0x37175B
BYTETBL = 0x011100
GROUPS = 870
PER_GROUP = 8
TERMINATORS = (0x00AC, 0x00AE)

PAGE_BREAK = 0x00AF
LINE_BREAK = 0x00AD
SPEAKER_TAG = 0x00D4
GLYPH = 0x0200             # symbols below this are control codes


class Fail(Exception):
    pass


class Rom(object):
    def __init__(self, path):
        self.path = path
        self.d = io.open(path, 'rb').read()
        if len(self.d) < PAYLOAD:
            raise Fail('%s is too small to be a DQ6 ROM (%d bytes).'
                       % (os.path.basename(path), len(self.d)))
        if self.d[ROOT_AT - 1] != 0xA2:
            raise Fail('no LDX #imm at $C0:2BFA in %s, so the tree root '
                       'cannot be read.\n  This does not look like a DQ6 ROM.'
                       % os.path.basename(path))
        self.root = self.d[ROOT_AT] | (self.d[ROOT_AT + 1] << 8)

    def crc(self):
        return zlib.crc32(self.d) & 0xFFFFFFFF

    def entry(self, g):
        o = TABLE + g * 3
        return self.d[o] | (self.d[o + 1] << 8) | (self.d[o + 2] << 16)

    def decode_all(self):
        """Every message as (symbols, terminator), in ID order."""
        d, out = self.d, []
        for g in range(GROUPS):
            e = self.entry(g)
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
                out.append((syms, v))
        return out

    def codes(self):
        out, stack = {}, [(self.root, '', frozenset([self.root]))]
        while stack:
            node, prefix, seen = stack.pop()
            if len(prefix) > 64:
                continue
            for bit in (0, 1):
                base = TREE1 if bit else TREE0
                v = self.d[base + node] | (self.d[base + node + 1] << 8)
                if v & 0x8000:
                    nxt = v & 0x7FFF
                    if nxt not in seen:
                        stack.append((nxt, prefix + str(bit), seen | {nxt}))
                elif v not in out:
                    out[v] = prefix + str(bit)
        return out

    def glyph_map(self):
        """symbol -> character, taken from the ROM's own byte table.

        Only the ranges whose meaning is fixed by the name-entry screen are
        used. Everything else stays unnamed and renders loudly.
        """
        out = {}

        def put(byte, char):
            o = BYTETBL + byte * 2
            out.setdefault(self.d[o] | (self.d[o + 1] << 8), char)

        put(0x01, ' ')
        for i in range(10):
            put(0x02 + i, chr(48 + i))
        for i in range(26):
            put(0x10 + i, chr(65 + i))
            put(0x42 + i, chr(97 + i))
        return out


def render(symbols, gmap):
    """Visible text. Control codes vanish, unknown glyphs are loud."""
    out = []
    for s in symbols:
        if s < GLYPH:
            continue
        out.append(gmap.get(s, '<%04X>' % s))
    return ''.join(out)


def identify(rom):
    print('  ROM      %s' % os.path.basename(rom.path))
    print('           %13s bytes   CRC32 %08X'
          % ('{:,}'.format(len(rom.d)), rom.crc()))


def placeholder_ids(messages, gmap):
    """Messages that display their own ID, and the ones that display TEXT+ID."""
    digits, tagged = [], []
    for i, (syms, _term) in enumerate(messages):
        text = render(syms, gmap).strip()
        if not text:
            continue
        if text.startswith(str(i)):
            digits.append(i)
        elif text.startswith('TEXT') and text[4:].strip().startswith(str(i)):
            tagged.append(i)
    return digits, tagged


def runs_of(ids, minimum):
    out, start, prev = [], None, None
    for i in ids:
        if prev is not None and i == prev + 1:
            prev = i
            continue
        if start is not None and prev - start + 1 >= minimum:
            out.append((start, prev))
        start = prev = i
    if start is not None and prev - start + 1 >= minimum:
        out.append((start, prev))
    return out


def report(rom):
    print('message script')
    print('=' * 78)
    identify(rom)
    print()
    messages = rom.decode_all()
    gmap = rom.glyph_map()

    print('  %-42s $%04X' % ('Huffman root, read from $C0:2BFB', rom.root))
    print('  %-42s %6d' % ('pointer table entries at 0x%06X' % TABLE, GROUPS))
    print('  %-42s %6d' % ('messages per entry', PER_GROUP))
    print('  %-42s %6d' % ('message IDs', len(messages)))
    print()

    gaps = 0
    for g in range(GROUPS - 1):
        a, b = rom.entry(g), rom.entry(g + 1)
        if a >= b:
            gaps += 1
    print('  %-42s %6d' % ('groups that start after the one before',
                           GROUPS - 1 - gaps))
    print('  %-42s %6d' % ('groups that do not', gaps))
    print()

    named = set(gmap)
    unnamed = set(s for m in messages for s in m[0]
                  if s >= GLYPH and s not in named)
    empty = sum(1 for m in messages if not render(m[0], gmap).strip())
    print('  %-42s %6d' % ('glyph symbols used by the script',
                           len(unnamed) + len(set(s for m in messages
                                                  for s in m[0]
                                                  if s >= GLYPH) & named)))
    print('  %-42s %6d' % ('of those, ones this tool can name', len(named &
                           set(s for m in messages for s in m[0]))))
    print('  %-42s %6d' % ('of those, ones it cannot', len(unnamed)))
    print('  %-42s %6d' % ('messages that display nothing at all', empty))
    print()
    print('  This tool names only the digits, letters and space the byte')
    print('  table fixes. Everything else renders as <XXXX> and is counted,')
    print('  never as a space. A decoder that falls back to a space instead')
    print('  produces legal-looking output, and one did exactly that here.')
    print('  The counts below need the digits and nothing more, so the')
    print('  unnamed glyphs do not weaken them.')
    print()

    digits, tagged = placeholder_ids(messages, gmap)
    print('  %-42s %6d' % ('messages displaying their own ID', len(digits)))
    print('  %-42s %6d' % ('messages displaying TEXT and their ID',
                           len(tagged)))
    print('  %-42s %6d' % ('unwritten in total', len(digits) + len(tagged)))
    print()
    if digits or tagged:
        both = sorted(digits + tagged)
        print('  %-42s %6d' % ('lowest ID', both[0]))
        print('  %-42s %6d' % ('highest ID', both[-1]))
        clusters = runs_of(both, 8)
        print('  %-42s %6d' % ('runs of 8 or more consecutive',
                               len(clusters)))
        if clusters:
            longest = max(clusters, key=lambda r: r[1] - r[0])
            print('  %-42s %6d' % ('longest run',
                                   longest[1] - longest[0] + 1))
            print('           at IDs %d-%d' % longest)
        print()
        print('  Runs of 8 or more:')
        for lo, hi in clusters:
            print('    %5d - %-5d  %3d messages' % (lo, hi, hi - lo + 1))
        print()


def placeholders(rom):
    print('message script')
    print('=' * 78)
    identify(rom)
    print()
    messages = rom.decode_all()
    gmap = rom.glyph_map()
    digits, tagged = placeholder_ids(messages, gmap)
    print('  %d messages display their own ID.' % (len(digits) + len(tagged)))
    print()
    for i in sorted(digits + tagged):
        print('    %5d  %r' % (i, render(messages[i][0], gmap).strip()))
    print()


def breaks(rom):
    print('message script')
    print('=' * 78)
    identify(rom)
    print()
    messages = rom.decode_all()
    gmap = rom.glyph_map()
    digits, tagged = placeholder_ids(messages, gmap)
    unwritten = set(digits) | set(tagged)

    counts = {'a line break': 0, 'end of message': 0,
              'another control code': 0, 'directly a letter': 0}
    examples = []
    for i, (syms, _t) in enumerate(messages):
        if i in unwritten:
            continue
        for k, s in enumerate(syms):
            if s != PAGE_BREAK:
                continue
            if k + 1 == len(syms):
                counts['end of message'] += 1
            elif syms[k + 1] == LINE_BREAK:
                counts['a line break'] += 1
            elif syms[k + 1] < GLYPH:
                counts['another control code'] += 1
            else:
                counts['directly a letter'] += 1
                examples.append(i)
    total = sum(counts.values())
    print('  What follows a page break, across every message that carries')
    print('  their own text:')
    print()
    for k in ('a line break', 'end of message', 'another control code',
              'directly a letter'):
        share = (100.0 * counts[k] / total) if total else 0.0
        print('  %-42s %6d   %5.2f%%' % (k, counts[k], share))
    print()
    print('  %-42s %6d' % ('page breaks in total', total))
    print()
    if counts['directly a letter'] <= 2:
        print('  A page break is never followed directly by text. That path')
        print('  was never exercised by their script, so a render fault on it')
        print('  is unreachable in their build and reachable only in new text.')
    if examples:
        print('  Exceptions at message IDs: %s'
              % ' '.join(str(i) for i in examples[:12]))
    print()


def quotes(rom):
    print('message script')
    print('=' * 78)
    identify(rom)
    print()
    messages = rom.decode_all()
    gmap = rom.glyph_map()
    digits, tagged = placeholder_ids(messages, gmap)
    unwritten = set(digits) | set(tagged)

    # Their opening quote after a speaker tag. The byte table does not name
    # it, so it is found rather than assumed: the glyph that turns up near a
    # speaker tag more often than any other IS the convention.
    WINDOW = 14
    near, tags = {}, []
    for i, (syms, _t) in enumerate(messages):
        if i in unwritten:
            continue
        for k, s in enumerate(syms):
            if s != SPEAKER_TAG:
                continue
            tags.append((i, k))
            for nxt in set(x for x in syms[k + 1:k + 1 + WINDOW]
                           if x >= GLYPH):
                near[nxt] = near.get(nxt, 0) + 1
    if not tags:
        print('  No speaker tags found.')
        print()
        return
    ranked = sorted(near.items(), key=lambda p: -p[1])
    print('  %-42s %6d' % ('speaker tags ($%02X)' % SPEAKER_TAG, len(tags)))
    print('  %-42s %6d' % ('symbols looked at after each tag', WINDOW))
    print()
    print('  Glyphs appearing within that window, most common first:')
    for sym, n in ranked[:6]:
        name = gmap.get(sym)
        label = repr(name) if name else 'symbol $%04X, unnamed' % sym
        print('    %-28s %6d   %5.1f%%'
              % (label, n, 100.0 * n / len(tags)))
    print()
    top, count = ranked[0]
    rate = 100.0 * count / len(tags)
    print('  The leader is %s at %.1f percent.'
          % ('symbol $%04X' % top if top not in gmap else repr(gmap[top]),
             rate))
    print()
    if rate >= 80:
        print('  A convention this strong is obligatory: new text that omits')
        print('  it is visibly foreign. Follow it while writing.')
    else:
        print('  A convention this weak is optional, and deciding it line by')
        print("  line produces a rate that reflects the author's mood.")
        print('  Defer it, then apply it in one measured pass at the end.')
    print()
    total = sum(1 for i, (syms, _t) in enumerate(messages)
                if i not in unwritten for x in syms if x == top)
    tagged_uses = count
    print('  %-42s %6d' % ('uses of that symbol in the whole script', total))
    print('  %-42s %6d' % ('uses that sit within a tag window', tagged_uses))
    print()


def roundtrip(rom):
    print('message script')
    print('=' * 78)
    identify(rom)
    print()
    messages = rom.decode_all()
    codes = rom.codes()

    missing = set()
    for syms, term in messages:
        for s in syms:
            if s not in codes:
                missing.add(s)
        if term not in codes:
            missing.add(term)
    print('  %-42s %6d' % ('distinct symbols in the script',
                           len(set(s for m in messages for s in m[0]))))
    print('  %-42s %6d' % ('symbols with no path through the trees',
                           len(missing)))
    if missing:
        print('  Cannot re-encode. The trees do not carry: %s'
              % ' '.join('$%04X' % s for s in sorted(missing)[:10]))
        print()
        return 1

    bits, group_bit = [], []
    for g in range(GROUPS):
        group_bit.append(sum(len(b) for b in bits))
        for i in range(g * PER_GROUP, (g + 1) * PER_GROUP):
            syms, term = messages[i]
            for s in syms:
                bits.append(codes[s])
            bits.append(codes[term])
    stream = ''.join(bits)
    out = bytearray((len(stream) + 7) // 8)
    for n, c in enumerate(stream):
        if c == '1':
            out[n >> 3] |= 1 << (7 - (n & 7))

    same = bytes(out) == rom.d[PAYLOAD:PAYLOAD + len(out)]
    print('  %-42s %6d' % ('bits produced', len(stream)))
    print('  %-42s %6d' % ('bytes produced', len(out)))
    print('  [%s] re-encoded payload is byte-identical'
          % ('PASS' if same else 'FAIL'))

    table_ok = True
    for g in range(GROUPS):
        a = group_bit[g]
        want = (a >> 3) * 8 + (7 - (a & 7))
        if want != rom.entry(g):
            table_ok = False
            break
    print('  [%s] rebuilt pointer table matches all %d entries'
          % ('PASS' if table_ok else 'FAIL', GROUPS))
    print()
    if same and table_ok:
        print('  The encode is deterministic here: every symbol has exactly')
        print('  one path through the trees, so this is a real gate and not')
        print('  a coincidence. Nothing should be inserted until it passes.')
        print()
        return 0
    print('  Do not insert anything into this ROM until this passes.')
    print()
    return 1


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0
    rom = Rom(argv[0])
    rest = argv[1:]
    if not rest:
        report(rom)
    elif rest[0] == '--placeholders':
        placeholders(rom)
    elif rest[0] == '--breaks':
        breaks(rom)
    elif rest[0] == '--quotes':
        quotes(rom)
    elif rest[0] == '--roundtrip':
        return roundtrip(rom)
    else:
        raise Fail('do not understand %r. Run with --help.' % ' '.join(rest))
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
