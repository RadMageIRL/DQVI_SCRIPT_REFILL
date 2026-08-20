#!/usr/bin/env python3
"""Apply the DQ6 Script Refill patch without needing Flips.

  usage:  patchRM.py <DQ6 NoPrgress.sfc>
          patchRM.py <patch.bps> <rom.sfc> [out.sfc]

With one argument it looks for the .bps beside itself and writes the patched
ROM next to your input. Your original file is never modified.

This applies the BPS format and validates every checksum in it: the patch's own
CRC32, the source ROM's CRC32 before applying, and the output's CRC32 after. A
wrong ROM is refused rather than silently producing something broken, which is
the whole reason to prefer BPS over IPS.

Standard-library Python 3 only. No dependencies, nothing to install.

The result is identical to what Flips produces from the same patch:

    CRC32 1C535999   SHA-1 cfd082c2db827f52305fdf98d915e7b86d5fda52
"""
import glob
import hashlib
import io
import os
import sys
import zlib

EXPECT_SRC_CRC = 0xB545C548
EXPECT_DST_CRC = 0x1C535999
DEFAULT_PATCH = 'DQ6-SFC-NoPrgress-RM-ScriptRefill.bps'


class Fail(Exception):
    pass


def crc32(data):
    return zlib.crc32(data) & 0xFFFFFFFF


def describe(tag, path, data, sha=False):
    """Two short lines rather than one very long one, so it stays readable in
    a narrow terminal."""
    out = ['  %-8s %s' % (tag, os.path.basename(path)),
           '           %13s bytes   CRC32 %08X'
           % ('{:,}'.format(len(data)), crc32(data))]
    if sha:
        out.append('           SHA-1 %s' % hashlib.sha1(data).hexdigest())
    return chr(10).join(out)


def read_varint(patch, pos):
    value, shift = 0, 1
    while True:
        octet = patch[pos]
        pos += 1
        value += (octet & 0x7F) * shift
        if octet & 0x80:
            return value, pos
        shift <<= 7
        value += shift


def apply_bps(src, patch):
    """Apply a BPS patch, checking every checksum it carries."""
    if patch[:4] != b'BPS1':
        raise Fail('that file is not a BPS patch (bad magic).')

    if crc32(patch[:-4]) != int.from_bytes(patch[-4:], 'little'):
        raise Fail('the patch file itself is corrupt (its own CRC32 does not match).\n'
                   '  Download it again.')

    want_src = int.from_bytes(patch[-12:-8], 'little')
    want_dst = int.from_bytes(patch[-8:-4], 'little')
    if crc32(src) != want_src:
        raise Fail(
            'wrong source ROM.\n'
            '  this patch expects  CRC32 %08X\n'
            '  the ROM you gave is CRC32 %08X\n'
            '\n'
            '  It needs a HEADERLESS NoPrgress-translated ROM. A headered copy\n'
            '  is 512 bytes larger and will not match.' % (want_src, crc32(src)))

    pos = 4
    src_size, pos = read_varint(patch, pos)
    dst_size, pos = read_varint(patch, pos)
    meta_size, pos = read_varint(patch, pos)
    pos += meta_size
    if src_size != len(src):
        raise Fail('source size mismatch: patch expects %d bytes, ROM is %d.'
                   % (src_size, len(src)))

    out = bytearray()
    src_rel = dst_rel = 0
    end = len(patch) - 12
    while pos < end:
        action, pos = read_varint(patch, pos)
        kind = action & 3
        length = (action >> 2) + 1
        if kind == 0:                                    # SourceRead
            start = len(out)
            out += src[start:start + length]
        elif kind == 1:                                  # TargetRead
            out += patch[pos:pos + length]
            pos += length
        elif kind == 2:                                  # SourceCopy
            raw, pos = read_varint(patch, pos)
            src_rel += (-1 if raw & 1 else 1) * (raw >> 1)
            out += src[src_rel:src_rel + length]
            src_rel += length
        else:                                            # TargetCopy
            raw, pos = read_varint(patch, pos)
            dst_rel += (-1 if raw & 1 else 1) * (raw >> 1)
            for _ in range(length):
                out.append(out[dst_rel])
                dst_rel += 1

    if len(out) != dst_size:
        raise Fail('output size mismatch: expected %d bytes, produced %d.'
                   % (dst_size, len(out)))
    if crc32(bytes(out)) != want_dst:
        raise Fail('output CRC32 mismatch - the patch did not apply cleanly.')
    return bytes(out)


def find_patch():
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(here, DEFAULT_PATCH), DEFAULT_PATCH):
        if os.path.exists(cand):
            return cand
    hits = glob.glob(os.path.join(here, '*.bps')) or glob.glob('*.bps')
    if len(hits) == 1:
        return hits[0]
    raise Fail('cannot find %s. Put it beside this script, or pass it as the\n'
               '  first argument.' % DEFAULT_PATCH)


def main(argv):
    if len(argv) == 1:
        patch_path = find_patch()
        rom_path = argv[0]
        out_path = None
    elif len(argv) in (2, 3):
        patch_path, rom_path = argv[0], argv[1]
        out_path = argv[2] if len(argv) == 3 else None
    else:
        print(__doc__.strip().split('\n\n')[1])
        return 2

    if out_path is None:
        stem, ext = os.path.splitext(rom_path)
        out_path = stem + ' (Script Refill)' + (ext or '.sfc')

    print('DQ6 Script Refill')
    print('=' * 78)
    patch = io.open(patch_path, 'rb').read()
    src = io.open(rom_path, 'rb').read()
    print(describe('patch', patch_path, patch))
    print(describe('source', rom_path, src))
    if crc32(src) == EXPECT_DST_CRC:
        raise Fail('that ROM is already patched. Start from an unpatched one.')

    out = apply_bps(src, patch)

    if os.path.abspath(out_path) == os.path.abspath(rom_path):
        raise Fail('refusing to overwrite the source ROM. Choose another name.')
    io.open(out_path, 'wb').write(out)
    print(describe('wrote', out_path, out, sha=True))
    print()
    if crc32(out) == EXPECT_DST_CRC:
        print('  All checksums verified. This is the released build.')
    else:
        print('  WARNING: applied cleanly, but the result is not the expected')
        print('  release build (CRC32 %08X).' % EXPECT_DST_CRC)
    print()
    print('  The patch contains everything: 421 messages, 179 name-table')
    print('  entries, both crash fixes, the gold window, and the redundant')
    print('  speech marker dropped. Nothing else to apply. Your original ROM')
    print('  was not modified.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Fail as exc:
        print('\nERROR: %s\n' % exc, file=sys.stderr)
        print('Nothing was written.', file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as exc:
        print('\nERROR: cannot open %s\n' % exc.filename, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
