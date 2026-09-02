# The patch, targeting the RHDN 344 build of the ROM

This is the same patch producing the same output ROM as the one in the
repository root, targeting a different source. Applying RHDN translation 344
yourself gives a ROM with CRC32 `276D9893`, which is the same translation as
`B545C548` differing in four bytes at `0x00FFDC`-`0x00FFDF`: that patch leaves
the Japanese ROM's own internal checksum in place instead of recomputing it over
the translated data. `DQ6-SFC-NoPrgress-RM-ScriptRefill-RHDN.bps` expects
`276D9893` and refuses `B545C548`, exactly as the root one does in reverse, and
both produce `CRC32 73B4B888` / `SHA-1 5bdc362472431117a0839ddbd1de8fed2ae4f8e0`.
The `.ips` is byte-identical to the one in the root, because IPS records only the
bytes to write and both sources differ from the output in the same places; it is
here so this directory is complete on its own.

| File | Size | SHA-1 |
|---|---:|---|
| `DQ6-SFC-NoPrgress-RM-ScriptRefill-RHDN.bps` | 213,345 | `c623a4b003f02da3b54ece17c77305ad6efbd137` |
| `DQ6-SFC-NoPrgress-RM-ScriptRefill-RHDN.ips` | 294,523 | `1676a58eb2a180af16d2d1488f32adc27bf3b250` |

`patchRM.py` in the root needs none of this. It takes either ROM with either
patch, corrects the four bytes in memory to match whichever patch you gave it,
and never modifies your file.
