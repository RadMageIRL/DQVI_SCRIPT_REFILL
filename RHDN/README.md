# The patch, targeting the RHDN 344 build of the ROM

This is the same patch producing the same output ROM as the one in the
repository root, targeting a different source. Applying RHDN translation 344
yourself gives a ROM with CRC32 `276D9893`, which is the same translation as
`B545C548` differing in four bytes at `0x00FFDC`-`0x00FFDF`: that patch leaves
the Japanese ROM's own internal checksum in place instead of recomputing it over
the translated data. `DQ6-SFC-NoPrgress-RM-ScriptRefill-RHDN.bps` expects
`276D9893` and refuses `B545C548`, exactly as the root one does in reverse, and
both produce `CRC32 5AE41C1D` / `SHA-1 a56f86582ca1be63ae79c19894516acf2d129380`.
The `.ips` is byte-identical to the one in the root, because IPS records only the
bytes to write and both sources differ from the output in the same places; it is
here so this directory is complete on its own.

| File | Size | SHA-1 |
|---|---:|---|
| `DQ6-SFC-NoPrgress-RM-ScriptRefill-RHDN.bps` | 216,443 | `0b13c6725293d4de89032bd61df8677eb42ec0a1` |
| `DQ6-SFC-NoPrgress-RM-ScriptRefill-RHDN.ips` | 294,036 | `532868df74fdff87deb665a568fae5a8089521c2` |

`patchRM.py` in the root needs none of this. It takes either ROM with either
patch, corrects the four bytes in memory to match whichever patch you gave it,
and never modifies your file.
