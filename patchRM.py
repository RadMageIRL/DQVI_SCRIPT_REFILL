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

It accepts either of the two NoPrgress ROMs in circulation, paired with either
patch: CRC32 B545C548, and CRC32 276D9893, which is what RHDN translation 344
produces and which is the same translation with the Japanese ROM's internal
checksum still in it. Whichever pairing you have, the four bytes are corrected
in memory to match the patch. Your file is not modified.

Standard-library Python 3 only. No dependencies, nothing to install.

The result is identical to what Flips produces from the same patch:

    CRC32 5AE41C1D   SHA-1 a56f86582ca1be63ae79c19894516acf2d129380
"""
import glob
import hashlib
import io
import os
import sys
import zlib

EXPECT_SRC_CRC = 0xB545C548
EXPECT_DST_CRC = 0x5AE41C1D
DEFAULT_PATCH = 'DQ6-SFC-NoPrgress-RM-ScriptRefill.bps'
NL = chr(10)

# The ordinary route is RHDN translation 344 applied to a headered Japanese
# ROM. That produces the same translation as EXPECT_SRC_CRC, byte for byte,
# except for four bytes: the patch leaves the Japanese ROM's own internal
# checksum in place rather than recomputing it for the patched data.
#
# MEASURED, 2026-08-29: RHDN 344 applied to CRC32 33304519 with a 512-byte
# header gives CRC32 8D2AEBD5; with the header removed it gives 276D9893, which
# differs from B545C548 only at 0x00FFDC-0x00FFDF.
#
# Both are accepted here. The four bytes are corrected in memory, and the file
# on disk is never touched.
RHDN_SRC_CRC = 0x276D9893
CHECKSUM_AT = 0x00FFDC
CHECKSUM_STALE = bytes([0x70, 0xA1, 0x8F, 0x5E])   # complement $A170, sum $5E8F
CHECKSUM_FIXED = bytes([0x85, 0x2E, 0x7A, 0xD1])   # complement $2E85, sum $D17A


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


def bps_source_crc(patch):
    """The CRC32 of the ROM a BPS patch expects, read without applying it."""
    if len(patch) < 12 or patch[:4] != b'BPS1':
        return None
    return int.from_bytes(patch[-12:-8], 'little')


def normalize(src, want_src):
    """Bridge the two NoPrgress builds, which differ only in the checksum.

    Returns (rom, note). If the ROM given is the other build of the same
    translation, the four checksum bytes are corrected in memory to whatever
    the patch expects, in either direction. Anything else comes back
    untouched, so a genuinely wrong ROM still fails the check in apply_bps
    rather than being quietly adjusted into something.
    """
    if want_src is None or len(src) != 0x400000 or crc32(src) == want_src:
        return src, None
    for pair in (CHECKSUM_FIXED, CHECKSUM_STALE):
        out = bytearray(src)
        out[CHECKSUM_AT:CHECKSUM_AT + 4] = pair
        out = bytes(out)
        if crc32(out) == want_src:
            note = ('your ROM and this patch are the two builds of the same '
                    'translation,' + NL +
                    '           CRC32 %08X and %08X, four bytes apart at '
                    '0x%06X: the' % (crc32(src), want_src, CHECKSUM_AT) + NL +
                    '           internal checksum. Corrected in memory to '
                    'match the patch. Your' + NL +
                    '           file was not modified.')
            return out, note
    return src, None


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
        detail = ('\n\n  It needs the NoPrgress-translated ROM, CRC32 %08X, or the\n'
                  '  RHDN 344 build, CRC32 %08X, which this script corrects for you.'
                  % (EXPECT_SRC_CRC, RHDN_SRC_CRC))
        if len(src) == 0x400000 + 512:
            detail = ('\n\n  That file is 512 bytes larger than a headerless ROM, so it\n'
                      '  carries a copier header. Remove the header and try again.')
        elif len(src) != 0x400000:
            detail = ('\n\n  That file is %s bytes. A headerless SNES DQ6 image is\n'
                      '  4,194,304.' % '{:,}'.format(len(src)))
        raise Fail(
            'wrong source ROM.\n'
            '  this patch expects  CRC32 %08X\n'
            '  the ROM you gave is CRC32 %08X%s' % (want_src, crc32(src), detail))

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

    src, note = normalize(src, bps_source_crc(patch))
    if note:
        print('  note     %s' % note)

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
    print('  The patch contains everything: 421 messages, 187 name-table')
    print('  entries, both crash fixes, the Tactics-equip hang, the gold')
    print("  window, clymax's in-battle spell target fix, and the redundant")
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
