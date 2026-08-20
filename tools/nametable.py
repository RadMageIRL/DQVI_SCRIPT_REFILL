#!/usr/bin/env python3
"""Read the DQ6 name table out of a ROM and check what the docs claim about it.

  usage:  nametable.py <rom.sfc> [option]

  (none)             structural report: groups, aliasing, reachable entries,
                     and the identifier-displaying entries the ID rule is about
  --untranslated     every entry that displays its own identifier
  --id HEX[,HEX..]   resolve specific string IDs, the way the game resolves them
  --widths [LO-HI]   line lengths per region, measured from the ROM's own text
  --breaks           check the break-code rule (code = 0x90 + length of line 1)
  --ligatures        solve the dictionary codes' displayed lengths from the
                     break codes alone, and compare against the table below
  --check FILE       resolve every string ID in a nametable-en.txt and report
                     which ones do not display what the file says they should

You supply the ROM. Nothing else is needed and nothing is written.

The name table is the second string system in DQ6: item, spell, skill, place,
monster-action and menu names, byte-encoded rather than Huffman-coded, packed
end to end and $AC-terminated. docs/NAME-TABLE.md describes it. This tool reads
it back out so those claims can be checked rather than taken on trust.

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

# Regions used for the per-region caps in docs/NAME-TABLE.md, as entry
# positions. They were found by reading the table, not assumed: see --widths
# with no range for the block map they come from.
REGIONS = (('battle actions', 1088, 1279),
           ('skill descriptions', 1280, 1631),
           ('menu / status', 192, 319),
           ('place names', 416, 543))

# Dictionary codes. Three of these carry a SPACE, which is easy to miss because
# a decoder that drops it still produces readable English. --ligatures derives
# every length from the break codes and will say so if this table is wrong.
LIGATURES = {
    0xC8: 'l',  0xC9: 'a',  0xCA: 'd',  0xCB: ' t', 0xCC: 'w',  0xCD: 'ac',
    0xCE: 'am', 0xCF: 'an', 0xD0: 'ar', 0xD1: 'as', 0xD2: 'at', 0xD3: 'ce',
    0xD4: 'ch', 0xD5: 'ck', 0xD6: 'e',  0xD7: 'ea', 0xD8: 'ed', 0xD9: 'ee',
    0xDA: 'er', 0xDB: 'es', 0xDC: 'gh', 0xDD: 'he', 0xDE: 'ic', 0xDF: 'in',
    0xE0: 'is', 0xE1: 'it', 0xE2: 'le', 0xE3: 'll', 0xE4: 'ly', 0xE5: 'nd',
    0xE6: 'no', 0xE7: 'nt', 0xE8: 'of', 0xE9: 'oi', 0xEA: 'on', 0xEB: 'oo',
    0xEC: 'or', 0xED: 'ou', 0xEE: 'ow', 0xEF: 'ra', 0xF0: 're', 0xF1: 'ro',
    0xF2: 's ', 0xF4: 'so', 0xF5: 'st', 0xF6: 'age', 0xF7: 't ', 0xF8: 'te',
    0xF9: 'th', 0xFA: 'us'}

# Single glyphs that sit inside the $82-$9D range and are NOT break codes.
GLYPHS = {0x82: '/', 0x85: ':', 0x88: '-', 0x89: '*', 0x8B: ','}

BREAK_LO, BREAK_HI = 0x91, 0x9D          # 0x90 + 1 .. 0x90 + 13

# An entry that was never translated displays the game's own identifier.
IDENTIFIER = re.compile(r'^([A-Za-z*])([0-9A-F]{2,4})$')


class Fail(Exception):
    pass


def decode(raw):
    """What the game displays for one entry. '|' marks a line break."""
    out = []
    for x in raw:
        if x == 0x01:
            out.append(' ')
        elif 0x02 <= x <= 0x0B:
            out.append(chr(48 + x - 0x02))
        elif 0x10 <= x <= 0x29:
            out.append(chr(65 + x - 0x10))
        elif 0x42 <= x <= 0x5B:
            out.append(chr(97 + x - 0x42))
        elif x == 0x77:
            out.append("'")
        elif x == 0x78:
            out.append('-')
        elif x in (0x7A, 0x7F):
            out.append('.')
        elif x == 0x79:
            out.append('?')
        elif x == 0x81:
            out.append('!')
        elif x == 0x0D:
            out.append('~')            # a control code that draws a tilde
        elif x in GLYPHS:
            out.append(GLYPHS[x])
        elif x in LIGATURES:
            out.append(LIGATURES[x])
        elif BREAK_LO <= x <= BREAK_HI:
            out.append('|')
        else:
            out.append('<%02X>' % x)   # loud, never mistakable for content
    return ''.join(out)


class Table(object):
    """The name table of one ROM, resolved the way $C0:315E resolves it."""

    def __init__(self, path):
        self.path = path
        self.rom = io.open(path, 'rb').read()
        if len(self.rom) < NT_END:
            raise Fail('%s is too small to be a DQ6 ROM (%d bytes).'
                       % (os.path.basename(path), len(self.rom)))

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

    def position(self, sid):
        """String ID -> entry position. group = ID >> 4, then walk ID & 15."""
        return self.groups[sid >> 4] + (sid & 0x0F)

    def text(self, sid):
        return decode(self.entries[self.position(sid)])

    def at(self, pos):
        return decode(self.entries[pos])

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
    print('  the table:')
    print()
    ok, bad = 0, []
    for pos in range(table.reachable):
        run = 0
        for x in table.entries[pos]:
            if BREAK_LO <= x <= BREAK_HI:
                if x == 0x90 + run:
                    ok += 1
                else:
                    bad.append((pos, table.at(pos), x, run))
                run = 0
            elif x in LIGATURES:
                run += len(LIGATURES[x])
            else:
                run += 1
    print('  %-42s %6d' % ('break codes consistent with the rule', ok))
    print('  %-42s %6d' % ('break codes that are not', len(bad)))
    for pos, t, x, run in bad[:20]:
        print('           %-5d %-30r says $%02X, line is %d long'
              % (pos, t, x, run))
    if len(bad) > 20:
        print('           ... and %d more' % (len(bad) - 20))
    print()
    if bad:
        print('  A failure here is usually not a bad break code. It is a')
        print('  dictionary code whose length this tool has wrong. Run')
        print('  --ligatures, which derives the lengths instead of assuming.')
        print()


def ligatures(table):
    """Solve each dictionary code's displayed length from the break codes.

    Every break code states how long the line before it is, so each one is an
    equation in the lengths of the codes on that line. Enough of them have a
    single unknown that the whole set falls out by substitution, and the
    remainder then act as a check. This needs no assumption about what any
    code SAYS, only that the break codes are correct, and it is the check
    that catches a code whose text quietly carries a space.
    """
    head(table)
    equations = []
    for pos in range(table.reachable):
        run = []
        for x in table.entries[pos]:
            if BREAK_LO <= x <= BREAK_HI:
                equations.append((list(run), x - 0x90))
                run = []
            else:
                run.append(x)
    print('  %d break codes give %d equations in the dictionary lengths.'
          % (len(equations), len(equations)))
    print()

    known, changed = {}, True
    while changed:
        changed = False
        for line, total in equations:
            rest, missing = total, []
            for b in line:
                if b >= 0xC8 and b not in known:
                    missing.append(b)
                else:
                    rest -= known.get(b, 1)
            if len(missing) == 1 and rest >= 0 and missing[0] not in known:
                known[missing[0]] = rest
                changed = True

    seen = set(b for line, _ in equations for b in line if b >= 0xC8)
    print('  %-42s %6d' % ('codes appearing in those lines', len(seen)))
    print('  %-42s %6d' % ('lengths solved', len(known)))
    print()
    wrong = []
    for b in sorted(known):
        assumed = LIGATURES.get(b)
        if assumed is None:
            wrong.append((b, known[b], None))
        elif len(assumed) != known[b]:
            wrong.append((b, known[b], assumed))
    if wrong:
        print('  MISMATCH against the table in this file:')
        for b, measured, assumed in wrong:
            print('    $%02X  measured %d characters, table says %r (%d)'
                  % (b, measured, assumed, len(assumed or '')))
        print()
    else:
        print('  Every solved length matches the table in this file.')
        print()

    ok, bad = 0, 0
    for line, total in equations:
        if any(b >= 0xC8 and b not in known for b in line):
            continue
        if sum(known.get(b, 1) for b in line) == total:
            ok += 1
        else:
            bad += 1
    print('  %-42s %6d' % ('equations satisfied by the solution', ok))
    print('  %-42s %6d' % ('equations left unsatisfied', bad))
    print()
    unsolved = sorted(seen - set(known))
    if unsolved:
        print('  Not solved, because no equation isolated them: %s'
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
        print('  Run --ligatures before concluding the ROM is wrong.')
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
    elif rest[0] == '--ligatures':
        ligatures(table)
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
