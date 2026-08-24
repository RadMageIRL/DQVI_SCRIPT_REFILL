# The three hang fixes

This patch contains all three hang fixes from
[DQVI_NOPRGRESS_MENU_FIX](https://github.com/RadMageIRL/DQVI_NOPRGRESS_MENU_FIX),
so you do not need to apply that patch as well.

**`build.py` applies them itself.** It does not consume a patch file from that
repository, and it does not need a Japanese ROM as a donor - the 87-byte
restoration, all 21 Forget sites and the 84-byte equip hook are embedded in the
script, with each site checked before anything is written. That repository has
the full analysis; this one is self-contained.

**Two of the three are the translation's, and the third is not.** Info > All and
Forget are the same kind of accident, and neither is a design decision: bytes
removed to make room, with the surrounding code padded so addresses still lined
up. The Tactics-equip hang is in Enix's 1995 code and is present in the Japanese
ROM; only English data ever drives it into the failing state.

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

## Tactics equip

**What goes wrong.** Cycle in and out of a character's equipment through the
Tactics menu enough times and the game stops responding. The music keeps playing
and nothing accepts input.

**The cause.** `$C3:1AB1` is a broken duplicate of `$C3:1D0E`. Both decide where
the cursor should go when it sits on an entry that cannot be selected.
`$C3:1D0E` saves the ordinal, honours the carry `$C3:1B1E` returns, checks the
floor, and if there is nothing below, restores and searches upward against a
ceiling. `$C3:1AB1` steps back once, unconditionally, and commits.

One step past zero asks `$C3:1B1E` for an ordinal it cannot supply. **That
routine is not at fault** - it is bounded and it returns with the carry set, the
way this codebase reports failure. Its caller never looks. The sentinel is then
packed as though it were a screen position:

```
linear = (112/2)*16 + 1 = 897      row = 897>>5 = 28      col = 897&31 = 1
```

The tilemap is `$3068`-`$3767`, exactly 28 rows, so `$3068 + 28*64 = $3768`.
Row 28 is not merely off the end: it is precisely the cursor bitmap the same
code reads. The write corrupts the structure the next read depends on, which is
why the fault needs repeated cycling to start and never recovers once it has.

**Four of the eight callers of `$C3:1B1E` honour its carry and four do not**, and
all the damage arrived through those four. Five builds that patched consumers
each moved the fault to the next one.

**The fix.** Mirror `$C3:1D0E`'s search into `$C3:1AB1`, as a hook in verified
free space at `$C3:FC80`. The initial check and the redraw are untouched, so
ordinary cursor movement is byte-identical.

**The behavioral change, stated plainly.** The cursor may land on a different
entry than before in edge cases, because it now searches down to the floor and
up to the ceiling instead of stepping back once. That is `$C3:1D0E`'s intended
behavior and what the game does everywhere else, but it is a visible change
rather than a pure bug fix.

**Verification.** Confirmed in play, then checked against a trace of the fixed
build: the out-of-range sentinel reaches none of the four consumers, the ordinal
never goes negative, nothing writes row 28, `$376B` holds `$0000` throughout, and
the scan that used to spin exits cleanly on all 20 calls.

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
