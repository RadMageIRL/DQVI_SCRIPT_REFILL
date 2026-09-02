# The patch, targeting the RHDN 344 build of the ROM

This is the same patch producing the same output ROM as the one in the
repository root, targeting a different source. Applying RHDN translation 344
yourself gives a ROM with CRC32 `276D9893`, which is the same translation as
`B545C548` differing in four bytes at `0x00FFDC`-`0x00FFDF`: that patch leaves
the Japanese ROM's own internal checksum in place instead of recomputing it over
the translated data. `DQ6-SFC-NoPrgress-RM-ScriptRefill-RHDN.bps` expects
`276D9893` and refuses `B545C548`, exactly as the root one does in reverse, and
both produce `CRC32 64018C32` / `SHA-1 b58f349d3ae230b8c041ae0b414632e6e8b17de3`.
The `.ips` is byte-identical to the one in the root, because IPS records only the
bytes to write and both sources differ from the output in the same places; it is
here so this directory is complete on its own.

| File | Size | SHA-1 |
|---|---:|---|
| `DQ6-SFC-NoPrgress-RM-ScriptRefill-RHDN.bps` | 213,360 | `826cd257597ade11bdb0aa08c8af85b947e330b9` |
| `DQ6-SFC-NoPrgress-RM-ScriptRefill-RHDN.ips` | 294,518 | `ff42832628d5fdd111fd14d7453d355c6a955916` |

`patchRM.py` in the root needs none of this. It takes either ROM with either
patch, corrects the four bytes in memory to match whichever patch you gave it,
and never modifies your file.
