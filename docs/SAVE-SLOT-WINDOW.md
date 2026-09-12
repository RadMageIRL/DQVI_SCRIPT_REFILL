# The load screen's save-slot window

Why `Dhama Shrine` lost its last letter on the load screen, and the two bytes
that fixed it in v6.1.

---

## What it looked like

On `Continue A Quest`, each save slot draws one line:

```
1:Mike          Lv84  Dhama Shrin
```

The final `e` sat under the window frame. `Southern Gate` lost two letters.

It is not only clipping. The tilemap row is 32 cells wide and the text is not
bounded by the window, so an over-long name **wraps around the row** and draws
on the next line at the left of the screen. A ruler string written into the
place-name entry showed characters 14 and 15 appearing outside the box, over
the menu behind it.

---

## Measuring it

A throwaway build with `1234567890ABCDEFGHIJ` written into the location entry,
photographed at a known window size, gives the field width directly: each
character names its own position, so the last one visible is the answer.

Measured against a 32-cell screen, before the fix:

| | cell |
|---|---|
| window frame, left | 3.0 |
| cursor | 4.2 |
| `1:` + name field (8 characters) | 5 - 12 |
| `Lv84` | 14 - 16 |
| place name | 20 - 30 |
| window frame, right | 30.6 |

**Eleven cells** for the location. `Dhama Shrine` is 12 and `Southern Gate` is
13, so both overran, and the ruler confirmed the count exactly.

---

## The fix

The window is **descriptor 141** in the table at `$C5:7B5C`, 14 bytes per
entry with X, Y, W in the first three.

That table is identified from the code rather than from pattern matching: the
window-open routine at `$C3:736C` reads it through an inline argument whose
bytes are `5C 7B C5`. The same routine stores the window's left column into
`$388C`, and every field on the slot line is drawn at `$388C` plus an offset.
**So moving the window moves the whole line with it**, and no drawing code has
to change.

```
descriptor 141 at 0x058312
   X: 3 -> 1        two cells left
   W: 28 -> 30      right edge stays exactly where it was
```

Two bytes. The location field goes from 11 cells to **13**, which fits both
names above, and the wrap-around no longer happens for them.

The SNES internal checksum is unchanged, because `X` falls by 2 and `W` rises
by 2 and the two cancel in the sum.

`build.py` refuses to write unless descriptor 141 reads exactly `X=3 Y=6 W=28`,
the same guard the crash fixes and the gold window use.

---

## Why it stops at 13

**The window cannot grow outward.** Tested on hardware and in an emulator:
moving the left edge to cell 0, or extending the right edge to cell 31, puts
the frame where overscan cuts it. `X=1, W=30` is the practical limit in both
directions, so 13 cells is the ceiling this approach can reach.

**Two cells inside the line are still wasted** - one between the name field and
`Lv`, one between `Lv84` and the location. Reclaiming them would give 15
without touching the window at all, and that is the better fix. It was not
done because the gaps are not constants in the drawing code: this menu system
queues *fields* into a list at runtime (`$C3:7C95` writes them to `$3AC6`), and
the gaps come from dedicated spacer fields whose only body is `INC $388A`:

```
$C3:84BC   INC $388A / RTL          advance one cell
$C3:84C5   INC $388A / INC $388A    advance two
```

Those routines are shared across windows, so patching one blind would move text
on screens that are currently correct. Identifying which spacer this window
queues needs a runtime trace - a write breakpoint on `$7E:388A` while the load
screen draws - not static reading. Three separate column constants were tried
and rejected first: `$C3:913D` `+8`, `$C3:8927` `+9`, `$C3:8947` `+9`. All
three drive other screens; none moved this one.

---

## Scope, and what is not fixed

**This is the load screen only.** The in-game save screen, reached from a king
or a priest, is a *different window* that this release does not touch. It sits
nearly flush with the screen already, so it has far less slack.

**Long location names still overrun.** Of 94 location entries, 37 were longer
than the old 11 cells and **19 are still longer than 13**, including five at 17
characters (`Wild Horse Forest`, `Land of Happiness`, `Northern Mountain`,
`Dream-seeing Well`, `Herbal Hotsprings`). Whether any of them is a place the
game lets you save at has not been established. If one turns up in play, the
options are the two internal cells above, or shortening the name - and the
names are NoPrgress's, so that is not a change this project makes on its own.
