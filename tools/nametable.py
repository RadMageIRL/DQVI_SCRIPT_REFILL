#!/usr/bin/env python3
"""Read the DQ6 name table out of a ROM and check what the docs claim about it.

  usage:  nametable.py <rom.sfc> [option]

  (none)             structural report: groups, aliasing, reachable entries,
                     and the identifier-displaying entries the ID rule is about
  --untranslated     every entry that displays its own identifier
  --id HEX[,HEX..]   resolve specific string IDs, the way the game resolves them
  --widths [LO-HI]   line lengths per region, measured from the ROM's own text
  --breaks           check the break-code rule (code = 0x90 + length of line 1)
  --dictionary       the dictionary codes, read out of the ROM's own expander,
                     then checked a second way against the break codes
  --check FILE       resolve every string ID in a nametable-en.txt and report
                     which ones do not display what the file says they should

You supply the ROM. Nothing else is needed and nothing is written.

The name table is the second string system in DQ6: item, spell, skill, place,
monster-action and menu names, byte-encoded rather than Huffman-coded, packed
end to end and $AC-terminated. docs/NAME-TABLE.md describes it. This tool reads
it back out so those claims can be checked rather than taken on trust.

Nothing here is reconstructed from what the output looks like. The group table,
the charset and the dictionary all come out of the ROM, and --dictionary shows
a second, independent measurement agreeing with the first.

Standard-library Python 3 only. No dependencies, nothing to install.
"""
import io
import os
import re
import sys
import zlib

NT_PTR = 0x0165E7          # $C1:65E7, 3 bytes per group of 16 string IDs
NT_BASE = 0x3B8703         # string ID 0
NT_END = 0x3BC712          # end of the region
NT_GROUPS = 157            # groups 0..156, string IDs 0..2511
TERMINATOR = 0xAC

# The dictionary expander at $C3:FB23. Its CMP #imm gives the lowest
# dictionary code and its LDA long gives the table, so both are read rather
# than assumed. $FF terminates the table.
DICT_CMP = 0x03FB25
DICT_PTR = 0x03FB30

# Regions used for the per-region caps in docs/NAME-TABLE.md, as entry
# positions. They were found by reading the table, not assumed: see --widths
# with no range for the block map they come from.
REGIONS = (('battle actions', 1088, 1279),
           ('skill descriptions', 1280, 1631),
           ('menu / status', 192, 319),
           ('place names', 416, 543))

# Single-byte glyphs, including the five that sit inside the $82-$9D range and
# are NOT break codes.
GLYPHS = {0x01: ' ', 0x0D: '~', 0x77: "'", 0x78: '-', 0x79: '?', 0x7A: '.',
          0x7F: '.', 0x81: '!', 0x82: '/', 0x85: ':', 0x88: '-', 0x89: '*',
          0x8B: ','}

BREAK_LO, BREAK_HI = 0x91, 0x9D          # 0x90 + 1 .. 0x90 + 13

# An entry that was never translated displays the game's own identifier.
IDENTIFIER = re.compile(r'^([A-Za-z*])([0-9A-F]{2,4})$')


class Fail(Exception):
    pass


def base_char(x):
    """What one ordinary charset byte draws."""
    if x in GLYPHS:
        return GLYPHS[x]
    if 0x02 <= x <= 0x0B:
        return chr(48 + x - 0x02)
    if 0x10 <= x <= 0x29:
        return chr(65 + x - 0x10)
    if 0x42 <= x <= 0x5B:
        return chr(97 + x - 0x42)
    return '<%02X>' % x                  # loud, never mistakable for content


def read_dictionary(rom):
    """code -> the text it draws, read out of the ROM's own expander.

    Do not reconstruct this from decoded output. Ten of the fifty entries are
    a character longer than they look, because a sequence that begins or ends
    with a space still reads as fluent English with the space dropped.
    """
    first = rom[DICT_CMP] | rom[DICT_CMP + 1] << 8
    base = (rom[DICT_PTR] | rom[DICT_PTR + 1] << 8
            | (rom[DICT_PTR + 2] & 0x3F) << 16)
    if not 0xC0 <= first <= 0xFF or not 0 < base < len(rom) - 128:
        raise Fail('the dictionary expander at 0x%06X is not what this tool '
                   'expects.\n  Refusing to guess.' % DICT_CMP)
    out, i = {}, 0
    while rom[base + i * 2] != 0xFF:
        out[first + i] = base_char(rom[base + i * 2]) + \
            base_char(rom[base + i * 2 + 1])
        i += 1
        if i > 64:
            raise Fail('the dictionary table at 0x%06X does not terminate.'
                       % base)
    return first, base, out


class Table(object):
    """The name table of one ROM, resolved the way $C0:315E resolves it."""

    def __init__(self, path):
        self.path = path
        self.rom = io.open(path, 'rb').read()
        if len(self.rom) < NT_END:
            raise Fail('%s is too small to be a DQ6 ROM (%d bytes).'
                       % (os.path.basename(path), len(self.rom)))
        self.dict_first, self.dict_at, self.dict = read_dictionary(self.rom)

        self.entries, start = [], NT_BASE
        for i in range(NT_BASE, NT_END):
            if self.rom[i] == TERMINATOR:
                self.entries.append(self.rom[start:i])
                start = i + 1

        index_at, addr = {}, NT_BASE
        for n, e in enumerate(self.entries):
            index_at[addr] = n
            addr += len(e) + 1

        # Each group holds a 24-bit offset. $319C/$319E add $FB8703 to it WITH
        # the carry running into the bank byte; drop the carry and the table
        # looks corrupt from group 68 onward when in fact it is fine.
        self.groups = []
        for g in range(NT_GROUPS):
            o = NT_PTR + g * 3
            raw = self.rom[o] | self.rom[o + 1] << 8 | self.rom[o + 2] << 16
            a = (0xFB8703 + raw) & 0xFFFFFF
            key = ((a >> 16) & 0x3F) << 16 | (a & 0xFFFF)
            if key not in index_at:
                raise Fail(
                    'group %d points into the middle of an entry rather than '
                    'at the start of one.\n  The group table and the strings '
                    'do not line up, which is what happens when\n  the ROM is '
                    'not the NoPrgress translation: the base address $FB8703 '
                    'is\n  theirs, and another build packs the table '
                    'somewhere else.' % g)
            self.groups.append(index_at[key])

        self.reachable = max(self.groups) + 16
        self.first_id = {}
        for sid in range(NT_GROUPS * 16):
            self.first_id.setdefault(self.position(sid), sid)

    def decode(self, raw):
        """What the game displays for one entry. '|' marks a line break."""
        out = []
        for x in raw:
            if x in self.dict:
                out.append(self.dict[x])
            elif BREAK_LO <= x <= BREAK_HI:
                out.append('|')
            else:
                out.append(base_char(x))
        return ''.join(out)

    def position(self, sid):
        """String ID -> entry position. group = ID >> 4, then walk ID & 15."""
        return self.groups[sid >> 4] + (sid & 0x0F)

    def text(self, sid):
        return self.decode(self.entries[self.position(sid)])

    def at(self, pos):
        return self.decode(self.entries[pos])

    def crc(self):
        return zlib.crc32(self.rom) & 0xFFFFFFFF

    def identifiers(self):
        """(position, string ID, displayed text, prefix, claimed index)."""
        rows = []
        for pos in sorted(self.first_id):
            t = self.at(pos).strip()
            m = IDENTIFIER.match(t)
            if m:
                rows.append((pos, self.first_id[pos], t,
                             m.group(1), int(m.group(2), 16)))
        return rows

    def equations(self):
        """(bytes of a line, its stated length) for every break code."""
        out = []
        for pos in range(self.reachable):
            run = []
            for x in self.entries[pos]:
                if BREAK_LO <= x <= BREAK_HI:
                    out.append((list(run), x - 0x90))
                    run = []
                else:
                    run.append(x)
        return out

    def width(self, byte):
        return len(self.dict[byte]) if byte in self.dict else 1


def head(table):
    print('name table')
    print('=' * 78)
    print('  ROM      %s' % os.path.basename(table.path))
    print('           %13s bytes   CRC32 %08X'
          % ('{:,}'.format(len(table.rom)), table.crc()))
    print()


def report(table):
    head(table)
    shared = sum(1 for g in range(1, NT_GROUPS)
                 if table.groups[g] == table.groups[g - 1])
    print('  group table at 0x%06X, %d groups of 16 string IDs'
          % (NT_PTR, NT_GROUPS))
    print('  strings packed from 0x%06X, $%02X-terminated'
          % (NT_BASE, TERMINATOR))
    print('  dictionary at 0x%06X, %d codes from $%02X'
          % (table.dict_at, len(table.dict), table.dict_first))
    print()
    print('  %-42s %6d' % ('string IDs addressable', NT_GROUPS * 16))
    print('  %-42s %6d' % ('entries those IDs reach', table.reachable))
    print('  %-42s %6d' % ('IDs that alias onto an earlier entry',
                           NT_GROUPS * 16 - table.reachable))
    print('  %-42s %6d' % ('groups sharing a base with the one before',
                           shared))
    print('  %-42s %6d' % ('terminators found in the region',
                           len(table.entries)))
    print()

    rows = table.identifiers()
    resolves = [r for r in rows if r[3] in ('M', '*')]
    other = [r for r in rows if r[3] not in ('M', '*')]
    print('  entries displaying an identifier rather than text')
    print('  (test: one letter or "*", then 2 to 4 hex digits)')
    print()
    print('  %-42s %6d' % ('total', len(rows)))
    print('  %-42s %6d' % ('prefix M or *, so the index resolves',
                           len(resolves)))
    print('  %-42s %6d' % ('any other prefix, does not resolve', len(other)))
    if other:
        print('           %s' % ' '.join(sorted(set(r[2] for r in other))[:12]))
    print()

    exact = [r for r in resolves if r[4] == r[1]]
    print('  the ID rule')
    print()
    print('  %-42s %6d' % ('identifier equals the entry string ID',
                           len(exact)))
    print('  %-42s %6d' % ('identifier equals something else',
                           len(resolves) - len(exact)))
    print()
    if resolves and len(exact) == len(resolves):
        print('  Exactly, with no exceptions. An untranslated entry displays')
        print('  its own string ID in hex, so the Japanese it was meant to')
        print('  carry is whatever that same string ID resolves to in the')
        print('  Japanese ROM. Nothing has to be inferred.')
        print()
    if resolves:
        against = [r[4] - r[0] for r in resolves]
        print('  Why three shift theories came and went. Measured against the')
        print('  entry POSITION instead of the string ID, the same numbers')
        print('  look like a shift that will not settle:')
        print()
        print('  %-42s %6d' % ('smallest identifier minus position',
                               min(against)))
        print('  %-42s %6d' % ('largest identifier minus position',
                               max(against)))
        print('  %-42s %6d' % ('distinct values it takes',
                               len(set(against))))
        print()
        print('  Position and string ID part company because %d IDs alias'
              % (NT_GROUPS * 16 - table.reachable))
        print('  onto an earlier entry. A shift fitted on entries before the')
        print('  first collapse holds, then stops holding, which is how each')
        print('  of the three theories got verified and then applied wrongly.')
    print()


def untranslated(table):
    head(table)
    rows = table.identifiers()
    print('  %d entries display an identifier.' % len(rows))
    print()
    print('  %-6s %-6s %-10s %s' % ('pos', 'ID', 'displays', 'claimed index'))
    for pos, sid, t, prefix, idx in rows:
        note = '%d' % idx if prefix in ('M', '*') else 'does not resolve'
        print('  %-6d $%04X  %-10s %s' % (pos, sid, t, note))
    print()


def resolve(table, spec):
    head(table)
    for part in spec.replace(',', ' ').split():
        try:
            sid = int(part, 16)
        except ValueError:
            raise Fail('%r is not a hex string ID.' % part)
        if not 0 <= sid < NT_GROUPS * 16:
            raise Fail('string ID $%04X is outside 0000-%04X.'
                       % (sid, NT_GROUPS * 16 - 1))
        pos = table.position(sid)
        print('  $%04X   group %-4d position %-5d %r'
              % (sid, sid >> 4, pos, table.text(sid)))
        print('          bytes  %s' % table.entries[pos].hex(' '))
    print()


def visible_lines(text):
    return [ln for ln in text.split('|') if ln]


def widths(table, rng):
    head(table)
    if rng:
        m = re.match(r'^(\d+)-(\d+)$', rng)
        if not m:
            raise Fail('a range looks like 1088-1279.')
        regions = (('positions %s' % rng, int(m.group(1)), int(m.group(2))),)
    else:
        regions = REGIONS

    print('  Lines per region, counting what the game DISPLAYS. Entries that')
    print('  still show an identifier are excluded, since they are not their')
    print('  own text.')
    print()
    print('  %-22s %6s %5s %6s   %s'
          % ('region', 'lines', 'max', 'mean', 'longest'))
    for name, lo, hi in regions:
        lens, longest = [], ''
        for pos in range(lo, min(hi, table.reachable - 1) + 1):
            t = table.at(pos)
            if not t or IDENTIFIER.match(t.strip()):
                continue
            for ln in visible_lines(t):
                lens.append(len(ln))
                if len(ln) > len(longest):
                    longest = ln
        if not lens:
            print('  %-22s %6d' % (name, 0))
            continue
        print('  %-22s %6d %5d %6.1f   %r'
              % (name, len(lens), max(lens), sum(lens) / float(len(lens)),
                 longest))
    print()

    if not rng:
        print('  Where those regions come from. Maximum line length in each')
        print('  block of 32 entries, with the first few entries of the block:')
        print()
        for blk in range(0, table.reachable, 32):
            texts = [table.at(p)
                     for p in range(blk, min(blk + 32, table.reachable))]
            mx = 0
            for t in texts:
                for ln in visible_lines(t):
                    mx = max(mx, len(ln))
            sample = ' | '.join(t for t in texts[:3] if t)
            print('  %4d-%4d  max %2d  %s' % (blk, blk + 31, mx, sample[:44]))
        print()


def breaks(table):
    head(table)
    print('  A break code is 0x90 plus the number of characters the game has')
    print('  already drawn on that line. Checked against every break code in')
    print('  the table, using the dictionary widths read out of the ROM:')
    print()
    ok, bad = 0, []
    for line, stated in table.equations():
        drawn = sum(table.width(b) for b in line)
        if drawn == stated:
            ok += 1
        else:
            bad.append((line, stated, drawn))
    print('  %-42s %6d' % ('break codes consistent with the rule', ok))
    print('  %-42s %6d' % ('break codes that are not', len(bad)))
    for line, stated, drawn in bad[:20]:
        print('           %-30r says %d, line draws %d'
              % (''.join(table.decode(bytes(line))), stated, drawn))
    if len(bad) > 20:
        print('           ... and %d more' % (len(bad) - 20))
    print()
    if bad:
        print('  A failure here is usually not a bad break code. It is a')
        print('  width this tool has wrong. Run --dictionary.')
        print()


def dictionary(table):
    """Show the dictionary, then measure it a second, independent way.

    Every break code states how long the line before it is, so each one is an
    equation in the displayed widths of the codes on that line. Enough of them
    carry a single unknown for the whole set to fall out by substitution. That
    measures widths from the format's own internal consistency, with no appeal
    to what any code draws, and it agrees with the table read out of the ROM.
    """
    head(table)
    print('  Read out of the expander at $C3:FB23')
    print()
    print('  %-42s $%02X' % ('lowest dictionary code', table.dict_first))
    print('  %-42s 0x%06X' % ('table', table.dict_at))
    print('  %-42s %6d' % ('codes', len(table.dict)))
    print()
    row = []
    for code in sorted(table.dict):
        row.append('$%02X %-5r' % (code, table.dict[code]))
        if len(row) == 6:
            print('    ' + ' '.join(row))
            row = []
    if row:
        print('    ' + ' '.join(row))
    print()
    carriers = [c for c in sorted(table.dict) if ' ' in table.dict[c]]
    print('  %d of these draw a SPACE as part of the sequence: %s'
          % (len(carriers), ' '.join('$%02X' % c for c in carriers)))
    print('  Read a character short they still produce fluent English, so')
    print('  nothing looks wrong. That is why they are read from the ROM here')
    print('  rather than reconstructed from what the output looks like.')
    print()

    equations = table.equations()
    known, changed = {}, True
    while changed:
        changed = False
        for line, total in equations:
            rest, missing = total, []
            for b in line:
                if b in table.dict and b not in known:
                    missing.append(b)
                else:
                    rest -= known.get(b, 1)
            if len(missing) == 1 and rest >= 0 and missing[0] not in known:
                known[missing[0]] = rest
                changed = True

    print('  Measured a second way, from the break codes alone')
    print()
    print('  %-42s %6d' % ('break codes, so equations', len(equations)))
    seen = set(b for line, _ in equations for b in line if b in table.dict)
    print('  %-42s %6d' % ('codes appearing in those lines', len(seen)))
    print('  %-42s %6d' % ('widths solved by substitution', len(known)))
    disagree = [(b, known[b], table.dict[b]) for b in sorted(known)
                if known[b] != len(table.dict[b])]
    print('  %-42s %6d' % ('solved widths disagreeing with the ROM',
                           len(disagree)))
    for b, measured, text in disagree:
        print('           $%02X  break codes say %d, ROM says %r'
              % (b, measured, text))
    print()
    ok = bad = 0
    for line, total in equations:
        if any(b in table.dict and b not in known for b in line):
            continue
        if sum(known.get(b, 1) for b in line) == total:
            ok += 1
        else:
            bad += 1
    print('  %-42s %6d' % ('equations satisfied', ok))
    print('  %-42s %6d' % ('equations unsatisfied', bad))
    print()
    if not disagree:
        print('  Two independent measurements agree. One reads the table the')
        print('  renderer indexes; the other never looks at the table at all')
        print('  and derives the widths from the format having to be')
        print('  self-consistent. Neither asks what the output looks like.')
        print()
    unsolved = sorted(seen - set(known))
    if unsolved:
        print('  Not isolated by any equation, so measured only once: %s'
              % ' '.join('$%02X' % b for b in unsolved))
        print()


def check(table, path):
    head(table)
    want = {}
    for line in io.open(path, encoding='utf-8'):
        m = re.match(r'^([0-9A-Fa-f]{4})\s\s+(\S.*?)\s*$', line)
        if m:
            want[int(m.group(1), 16)] = m.group(2)
    if not want:
        raise Fail('no "<hex id>  <text>" rows in %s.' % path)

    print('  %s lists %d entries. Resolving each one out of this ROM:'
          % (os.path.basename(path), len(want)))
    print()
    bad = []
    for sid in sorted(want):
        got = table.text(sid)
        if got != want[sid]:
            bad.append((sid, want[sid], got))
    print('  %-42s %6d' % ('display what the file says', len(want) - len(bad)))
    print('  %-42s %6d' % ('do not', len(bad)))
    print()
    for sid, w, g in bad:
        print('    $%04X  file %-26r ROM %r' % (sid, w, g))
    if bad:
        print()
        print('  Run --dictionary before concluding the ROM is wrong.')
    print()
    return 1 if bad else 0


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0
    table = Table(argv[0])
    rest = argv[1:]
    if not rest:
        report(table)
    elif rest[0] == '--untranslated':
        untranslated(table)
    elif rest[0] == '--id' and len(rest) > 1:
        resolve(table, ' '.join(rest[1:]))
    elif rest[0] == '--widths':
        widths(table, rest[1] if len(rest) > 1 else None)
    elif rest[0] == '--breaks':
        breaks(table)
    elif rest[0] == '--dictionary':
        dictionary(table)
    elif rest[0] == '--check' and len(rest) > 1:
        return check(table, rest[1])
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
