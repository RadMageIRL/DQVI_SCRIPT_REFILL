# The two crash fixes

This patch contains both crash fixes from
[DQVI_NOPRGRESS_MENU_FIX](https://github.com/RadMageIRL/DQVI_NOPRGRESS_MENU_FIX),
so you do not need to apply that patch as well. They are summarised here so
this repository is self-contained; that repository has the full analysis.

Neither is a design decision by the translators. Both are the same kind of
accident: bytes removed to make room, with the surrounding code padded so
addresses still lined up.

## Info > All

**What goes wrong.** Open Info, choose All, and back out before the screen has
finished drawing. The game hangs.

**Cause.** A three-byte instruction, `STA $3AC2`, was deleted from `$C3:3538`.
It writes the party-slot loop bound. Without it the bound keeps a `$FF`
sentinel from the previous screen, the loop runs past the end of the party, and
the game trips an assertion Square left in at `$C4:560F`.

The deleted bytes were replaced by shifting the following three bytes back, so
every address after the deletion stayed where it was. That is what makes it
hard to spot in a byte diff: nothing moved.

**Fix.** Restore 87 bytes at `$C3:3538` from the Japanese ROM, which puts the
instruction back and undoes the shift. Verified at instruction level: after the
fix that span is byte-identical to the Japanese original.

**It matters at two party sizes.** The fault depends on how many slots the loop
walks, so a build should be tested with a small party and a full one.

## Forget

**What goes wrong.** The Forget conversation crashes.

**Cause.** Not a logic bug, and this took three failed branch fixes to find. It
is a **memory allocation collision**. Every instruction on the fault path is
byte-identical to the Japanese original; the defect is in *where* the
translation put its data.

The translation placed word-wrap state at `$7E:379E`, `$7E:37A0` and
`$7E:37A2`. Those addresses are inside a 112-byte block the original game
clears wholesale. The state is wiped mid-use.

**Fix.** Relocate that state to `$7E:55BE`, `$7E:55C0` and `$7E:55C2`, a region
established as unused. 19 sites, operands only - no opcode and no instruction
length changes - plus two branch conditions.

**The residual risk, stated plainly.** The destination region was chosen from
emulator code and data logs, two RAM snapshots, and instruction traces covering
field movement, dialogue, shops, menus and battle. No logged session covers
every context in the game, and code that has never executed cannot be ruled
out. Keep savestates the first time you use Forget.

## What these fixes do NOT do

The translation carries an **unbounded word-wrap fill**. The Forget fix
relocates the buffer out of harm's way and gives it 200 bytes of headroom
against a 136-byte worst case, but it does not bound the fill. That remains an
open defect in the translation and is not addressed here.

## Relationship to the gold window

The gold window was lost the same way and in the same routine: seven bytes
deleted at `$C3:3593`, four bytes after the `STA $3AC2` deletion, with the gap
padded by a duplicated `RTL` epilogue so downstream addresses stayed put.

Two deletions, the same technique, four bytes apart. The difference is why:
the `STA $3AC2` removal looks like a slip, while the gold removal was
deliberate - the status window had been widened for English stat labels and
the gold window no longer had anywhere to sit. See
[`GOLD-WINDOW.md`](GOLD-WINDOW.md).
