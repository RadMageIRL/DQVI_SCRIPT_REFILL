# The gold window

Technical record of the third thing this patch does. No ROM is distributed here
and none ever will be.

## The symptom

The Japanese game shows your gold in a window at the top right of the info
screen. The English translation shows nothing there at all.

## How it was found

Two emulator traces of the same screen, one per ROM. Every ROM address executed
during the Japanese trace was collected (14,839 unique), mapped to file offsets,
and compared byte for byte against the English ROM. That reduced the whole
problem to seven regions of divergence in code that demonstrably runs.

Diffing only what executed is the technique that also found the deleted
`STA $3AC2` behind the Info > All crash. It is much narrower than scanning for
constants, which on this ROM has produced false positives repeatedly.

## The cause

The window is drawn by a short routine at `$C3:358F`:

```
JAPANESE                          ENGLISH
$358F  JSL $C3736C                $358F  JSL $C3736C
$3593  LDA #$007A                 $3593  LDA #$003E
$3596  JSL $C3763A     <- gone    $3596  JSL $C383FE
$359A  LDA #$003E                 $359A  PLB / REP / PLY / PLX / PLA / PLP / RTL
$359D  JSL $C383FE                $35A2  REP / PLY / PLX / PLA / PLP / RTL   <- duplicate
$35A1  PLB / ... / RTL
```

Seven bytes deleted, `A9 7A 00 22 3A 76 C3`, and the gap padded with a
duplicated `RTL` epilogue so every downstream address stayed put. The same
padding technique appears four bytes earlier in the `STA $3AC2` deletion.

But the deletion is a **consequence**, not the defect. Window geometry lives in
a descriptor table at `$C5:7B5C`, 14 bytes per entry, indexed by `$3058`; gold
is entry 58, and bytes 11-13 of each entry are the draw routine pointer, which
is how it was identified. Comparing the entries:

```
Japanese   status cols 10-21   gold cols 22-30    side by side
English    status cols 10-24   gold cols 16-23    gold underneath the status window
```

English stat labels are wider than Japanese ones, the status window was widened
to fit them, and the gold window ended up inside it. With nowhere left to draw,
the call was removed. Restoring the seven bytes alone would have drawn a `G`
into covered coordinates.

## The fix

Twenty-five bytes.

```
0x033593   22 bytes   the draw call restored, at exact size
0x057E88    3 bytes   gold descriptor X=1 Y=1 W=9  (cols 1-9, rows 1-3)
```

- **Code.** The restored call is written over the English 15 bytes plus the dead
  duplicate epilogue, consuming it exactly. No relocation and no expansion
  space. The write ends at `$35A8`, one byte short of `$35A9`, which is the
  routine that opens the window.
- **Position.** Top left, where the English layout has room. Only the gold
  window's own descriptor changes.
- **The `G`.** It draws string `$10`, a bare one-byte `G`. Entry `$7A` is not a
  gold string at all: `$74`-`$7F` are ` A` through ` L`, an alphabet series in
  which every entry carries an `$88` prefix, and that prefix renders as a stray
  mark. `$10` is what the translation points its *other* gold window at, so this
  is their own substitution applied to the site they missed.

## Why it is contained

- Only descriptor `$3A` points at `$C3:358F`, so nothing else can enter the
  rewritten code.
- Only descriptor `$3A` differs from the stock translation. The status window,
  the command menu and every other window are byte-identical.
- The consumed epilogue follows an `RTL`, so nothing falls through to it, and
  the three `$35A2` byte-patterns elsewhere in the ROM sit in banks `$C9`,
  `$CD` and `$CF`, none of which can reach `$C3:35A2`.

Confirmed in play, together with Info > All at two party sizes.

## The correction trail

Two readings were wrong before this one, and both were instructive.

**"The labels are too wide, shrink them."** The first theory was that the UI
glyph table had been abandoned and labels rewritten as blank plus an ordinary
letter, making them wider. This was dismissed after measuring `HP` and `MP`,
which are two bytes in both ROMs and genuinely were untouched. **Generalising
from those two labels was the error.** The theory was right about the mechanism
- entries `$7A` and `$7B` did go from one byte to two - and wrong only about the
consequence. The widening is not what broke gold; the deleted call is.

**"They missed a site."** The second reading was that the translation had a
working substitution at their other gold window and simply forgot this one, so
the fix was seven bytes. Screenshots of both games side by side killed it: the
English status window visibly occupies the space, so the deletion was
deliberate. **The screenshots had been available the whole time.** Reasoning
from the disassembly alone produced a confident wrong conclusion that one look
would have prevented. The trace work was necessary to find the deleted call; it
was not sufficient to say what the deletion meant.
