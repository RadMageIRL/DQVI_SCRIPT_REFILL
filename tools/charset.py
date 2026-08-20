#!/usr/bin/env python3
"""Read the DQ6 text encoding out of a ROM: Huffman trees and the byte table.

  usage:  charset.py <rom.sfc> [option]

  (none)             the tree root, how many symbols are encodable, and the
                     byte-to-symbol table's collisions
  --symbols          every encodable symbol with its code length
  --symbol HEX       is this one symbol writable in this ROM, and at what cost
  --compare OTHER    the same figures for two ROMs side by side

You supply the ROM. Nothing else is needed and nothing is written.

Two things this answers that are easy to get wrong.

The tree ROOT is patched per ROM. It is read from the code at $C0:2BFB, not
assumed. Decoding one ROM with the other's root produces confident garbage
rather than an error, so it never announces itself.

The writable alphabet is the TREE, not the font. Insertion re-encodes with the
trees the ROM already has, so a symbol with no path through them cannot be
written whatever the font contains. "Does not appear in their text" and "cannot
be written" are different claims and only the second is a constraint.

Standard-library Python 3 only. No dependencies, nothing to install.
"""
import io
import os
import sys
import zlib

ROOT_AT = 0x002BFB         # operand of the LDX #imm at $C0:2BFA
TREE0 = 0x0167BE           # bit clear
TREE1 = 0x01700E           # bit set
BYTETBL = 0x011100         # byte -> symbol, 2 bytes per entry, 256 entries
TERMINATORS = (0x00AC, 0x00AE)


class Fail(Exception):
    pass


class Rom(object):
    def __init__(self, path):
        self.path = path
        self.d = io.open(path, 'rb').read()
        if len(self.d) < TREE1 + 0x2000:
            raise Fail('%s is too small to be a DQ6 ROM (%d bytes).'
                       % (os.path.basename(path), len(self.d)))
        if self.d[ROOT_AT - 1] != 0xA2:
            raise Fail('no LDX #imm at $C0:2BFA in %s, so the tree root cannot '
                       'be read.\n  This does not look like a DQ6 ROM.'
                       % os.path.basename(path))
        self.root = self.d[ROOT_AT] | (self.d[ROOT_AT + 1] << 8)

    def crc(self):
        return zlib.crc32(self.d) & 0xFFFFFFFF

    def symbol_of_byte(self, b):
        o = BYTETBL + b * 2
        return self.d[o] | (self.d[o + 1] << 8)

    def codes(self):
        """symbol -> bit string, by walking both trees from the root."""
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


def identify(rom):
    print('  ROM      %s' % os.path.basename(rom.path))
    print('           %13s bytes   CRC32 %08X'
          % ('{:,}'.format(len(rom.d)), rom.crc()))


def report(rom):
    print('text encoding')
    print('=' * 78)
    identify(rom)
    print()
    codes = rom.codes()
    lengths = sorted(len(c) for c in codes.values())
    print('  Huffman')
    print('  %-42s $%04X' % ('tree root, read from $C0:2BFB', rom.root))
    print('  %-42s 0x%06X / 0x%06X'
          % ('node tables (bit clear / bit set)', TREE0, TREE1))
    print('  %-42s %6d' % ('symbols reachable from that root', len(codes)))
    print('  %-42s %6d' % ('shortest code, in bits', lengths[0]))
    print('  %-42s %6d' % ('longest code, in bits', lengths[-1]))
    print('  %-42s %6.3f'
          % ('mean code length', sum(lengths) / float(len(lengths))))
    print('  %-42s %6s'
          % ('both terminators encodable',
             'yes' if all(t in codes for t in TERMINATORS) else 'NO'))
    print()

    control = sum(1 for s in codes if s < 0x200)
    print('  %-42s %6d' % ('of those, control codes (below $200)', control))
    print('  %-42s %6d' % ('of those, drawable glyphs', len(codes) - control))
    print()

    print('  Byte table at 0x%06X' % BYTETBL)
    print('  256 byte values, mapped to symbols. Bytes that share a symbol')
    print('  matter: sharing is how a control code hides behind a letter.')
    print()
    groups = {}
    for b in range(0x100):
        groups.setdefault(rom.symbol_of_byte(b), []).append(b)
    collide = [(s, bs) for s, bs in groups.items() if len(bs) > 1]
    collide.sort(key=lambda p: -len(p[1]))
    print('  %-42s %6d' % ('distinct symbols the 256 bytes reach',
                           len(groups)))
    print('  %-42s %6d' % ('symbols reached by more than one byte',
                           len(collide)))
    print()
    for s, bs in collide[:10]:
        run = ' '.join('$%02X' % b for b in bs[:14])
        if len(bs) > 14:
            run += ' ... (%d bytes)' % len(bs)
        print('    symbol $%04X   %s' % (s, run))
    print()
    print('  The four to look at are $0C $0D $0E $0F. Each shares a symbol')
    print('  with a real letter, so a decoder names them H, M, P and G, but')
    print('  the renderer takes them before the table is consulted and $0D')
    print('  draws a tilde. Encoding "M" as $0D gives "~adante 2".')
    print()
    for lo, hi in ((0x0C, 0x0F),):
        for b in range(lo, hi + 1):
            s = rom.symbol_of_byte(b)
            twins = [x for x in groups[s] if x != b]
            print('    $%02X -> symbol $%04X, shared with %s'
                  % (b, s, ' '.join('$%02X' % t for t in twins) or 'nothing'))
    print()


def symbols(rom):
    print('text encoding')
    print('=' * 78)
    identify(rom)
    print()
    codes = rom.codes()
    print('  %d encodable symbols, by symbol number.' % len(codes))
    print()
    for s in sorted(codes):
        print('    $%04X  %2d bits  %s' % (s, len(codes[s]), codes[s]))
    print()


def one_symbol(rom, spec):
    try:
        s = int(spec, 16)
    except ValueError:
        raise Fail('%r is not a hex symbol number.' % spec)
    print('text encoding')
    print('=' * 78)
    identify(rom)
    print()
    codes = rom.codes()
    if s in codes:
        print('  symbol $%04X is encodable: %d bits, %s'
              % (s, len(codes[s]), codes[s]))
    else:
        print('  symbol $%04X has no path through this ROM\'s trees.' % s)
        print('  It cannot be written here, whatever the font contains.')
    bytes_for = [b for b in range(0x100) if rom.symbol_of_byte(b) == s]
    if bytes_for:
        print('  The byte table reaches it from %s.'
              % ' '.join('$%02X' % b for b in bytes_for))
    print()


def compare(a, b):
    print('text encoding')
    print('=' * 78)
    identify(a)
    identify(b)
    print()
    ca, cb = a.codes(), b.codes()
    print('  %-30s %14s %14s' % ('', os.path.basename(a.path)[:14],
                                 os.path.basename(b.path)[:14]))
    print('  %-30s %14s %14s'
          % ('tree root', '$%04X' % a.root, '$%04X' % b.root))
    print('  %-30s %14d %14d' % ('encodable symbols', len(ca), len(cb)))
    print('  %-30s %14d %14d'
          % ('encodable in this one only',
             len(set(ca) - set(cb)), len(set(cb) - set(ca))))
    print('  %-30s %14d %14d'
          % ('encodable in both', len(set(ca) & set(cb)),
             len(set(ca) & set(cb))))
    print()
    if a.root != b.root:
        print('  The roots differ, which is the point: the root is patched')
        print('  per ROM. Decoding one with the other\'s root does not fail,')
        print('  it produces fluent nonsense.')
        print()


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0
    rom = Rom(argv[0])
    rest = argv[1:]
    if not rest:
        report(rom)
    elif rest[0] == '--symbols':
        symbols(rom)
    elif rest[0] == '--symbol' and len(rest) > 1:
        one_symbol(rom, rest[1])
    elif rest[0] == '--compare' and len(rest) > 1:
        compare(rom, Rom(rest[1]))
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
