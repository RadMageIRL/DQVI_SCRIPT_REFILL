# The in-battle spell target list

**This fix is clymax of ff5central.com's work, not mine.**

He wrote the one-byte patch for it, and it is carried in this one with his
permission.

What follows is my account of why his byte is the right byte, worked out from
the two ROMs afterwards. The reading is mine. The fix is his.

---

## What the player sees

In battle, choose Fight, then a spell that targets an ally. The list of targets
offers the whole caravan instead of just the character or characters who are in
the fight. You can point the cursor at somebody who is not there.

It only shows with somebody in the caravan. Before the caravan exists, and while
it is empty, the menu behaves correctly, which is part of why it went unnoticed.

## The patch

One record, one byte.

```
offset 0x0349D4   size 1   data 38
```

The ROM is HiROM and headerless, so file offset `X` is SNES `$C0:0000 + X` and
`0x0349D4` is `$C3:49D4`. That byte is the low half of an immediate operand:

```
            NoPrgress                        Enix, and after the fix
$C3:49D3    A9 16 00   LDA #$0016            A9 38 00   LDA #$0038
$C3:49D6    22 95 7C C3  JSL $C37C95         22 95 7C C3  JSL $C37C95
```

**The value being written is the value the Japanese ROM already has**, and the
bytes on either side of it are identical in both ROMs. This is a revert, not new
code. In this build it is applied by `apply_target_fix` in `build.py`, which
refuses to run if the site does not hold `0x16` first.

## What the site is

`$C3:7C95` appends one byte to a list at `$7E:3AC6`, counted by `$7E:3ADA`. So
`LDA #imm : JSL $C37C95` means "append menu entry *imm*". There are 402 such
calls in the ROM, forming 76 menus.

The menu here is built at `$C3:49BA`:

```
$C3:49BA   JSL $C3736C
           entries:  $6F  $87  $01  [$38 -> $16]  $22  $8A
           LDX #$0003
           JSL $C37854
```

`LDX #$0003` is an index, not a count. `$C3:7854` stores it at `$3ABE`, and
`$C3:7787` then reads `$3AC6,X` at that index and hands the result to
`$C3:A6E1`. Index 3 is the fourth entry, which is exactly the byte in question.
Of the six entries in this menu, the one clymax changes is the one the game
singles out to decide what the menu enumerates.

## Why one substitution out of fourteen broke

An entry ID is looked up in **two** separate Enix tables:

| table | keyed by | decides |
|---|---|---|
| `$C5:88FA`, 3-byte long pointers | entry ID | how the row is **drawn** |
| `$C3:A7C8`, 38 records of 3 bytes | entry ID | which roster is **enumerated** |

For the three IDs that matter:

```
              draw ($C5:88FA)                enumerate ($C3:A7C8)
        Enix           NoPrgress
$15     $C3:8744       $C3:8744  unchanged   $C3:A83A
$16     $C3:8744       $C3:99A6  REPOINTED   $C3:A85F
$38     $C3:87B4       $C3:87B4  unchanged   $C3:A896
```

In Enix's ROM, `$15` and `$16` draw through the same routine. That is what makes
`$16` look like a spare slot. It is not spare: it has its own record in the
enumeration table, and Enix use it in a menu of their own at `$C3:5D39`.

**The enumeration table is byte-identical in both ROMs.** NoPrgress changed six
entries of the draw table, `$16` among them, and none of the enumeration table.
That asymmetry is the whole defect. Repointing how something draws also changes
what it enumerates, because one ID keys both.

The reason for repointing `$16` was reasonable. Their new routine differs from
Enix's in a single value:

```
$C3:8744 (EN)   LDX $3AB4 / JSL $C44FA1 : 02 FE FF / LDX #$0008 / JSL $C3FA42
$C3:99A6 (EN)   LDX $3AB4 / JSL $C44FA1 : 02 FE FF / LDX #$0004 / JSL $C3FA42
$C3:87B4 (EN)   LDX $3AB4 / JSL $C44FA1 : 01 FE FF / LDX #$0004 / JSL $C3FA42
```

`$C3:FA42` is their own helper: it resolves the string ID in `A` and draws
exactly `X` characters, padding past the terminator. So `$8` and `$4` are a
field width, and their `$16` is `$15` at half the width. That is an English
fitting change and there is nothing wrong with it.

They then swept thirteen menus from `$15` to `$16` to get the narrower field,
and at `$C3:49D4` applied the same `$16` to an entry that was `$38`.

The first inline byte to `$C4:2B1C` is a list kind:

```
$C3:A83A   ($15)   JSL $C42B1C : 02 FD      kind $02
$C3:A85F   ($16)   JSL $C42B1C : 02 FF      kind $02
$C3:A896   ($38)   JSL $C42B1C : 01 FD      kind $01
```

**`$15` and `$16` are both kind `$02`.** They differ in where the count comes
back and in one extra filter, not in which roster they walk. So the thirteen
`$15` to `$16` edits moved the field width and left the list alone.

**`$38` is kind `$01`.** The fourteenth edit changed the list.

`$C4:2B1C` returns the list length, and the kind selects it in `$C4:2C6F`:

```
kind $01  ->  $C4:2CEC    count = $3F06,  bounded at 4
kind $02  ->  $C4:2D09    count = $3F07,  bounded at 8
                          but only if ($3F0A & 1) and not ($3F0A & 4);
                          otherwise it falls through to the kind $01 path
```

`$3F06` and `$3F07` are incremented together at `$C4:2F7E` and `$C4:2F81` and
decremented separately at `$C4:3455` and `$C4:346B`. With bounds of 4 and 8 and
a flag that gates the larger one, `$3F06` is the party in the battle and `$3F07`
is everyone travelling. The behavior on screen confirms it: a target list that
offers caravan members is those two rosters doing exactly what they are read to
do here.

That is also why the fault needs a non-empty caravan. `$3F0A` gates kind `$02`,
and with the gate closed it falls through to the kind `$01` path and is correct.

## The window was resized to match

Worth recording, because it says something about how the change was made.

```
         p0 p1 p2 p3 ...
JP       0e 12 0f 03      Enix
EN       0e 12 12 09      NoPrgress
```

This menu's record in the table at `$C5:7B67` was also edited. 107 of the 249
records were resized for English, so a resize on its own means nothing. But of
the 36 records whose `p3` changed, **35 changed by exactly one**. This one
changed by six, 3 to 9, and it is the only one that did.

The list got longer in rows, not in width. `$16` enumerates everyone
travelling, bounded at eight, where `$38` enumerates only those in the fight,
bounded at four, so a list of at most four names became a list of at most eight
and the window went from three rows to nine to hold them. Read plainly, they saw
the list get longer and made the window taller to fit it. So this was a
deliberate change with a consequence further down that was not foreseen, rather
than a careless find and replace. It does not change where the defect is.

## What this fix does not do

It reverts the entry ID and leaves the window resize alone, so the target box is
still the nine-row one sized for eight, now with at most four names in it.

What that looks like: the same box as before with fewer names in it. The height
comes from the record rather than from the number of names in the list, which is
why the record had to be edited to begin with, so reverting the list does not
shrink the box back. It reads correctly in play. Enix themselves pair a `$38`
list with a nine-row window elsewhere in the table, at record 122, so the
combination is one the game already ships.

I have deliberately not touched that. The fix is clymax's and it does what he
wrote it to do. Changing somebody else's patch because I have an opinion about
its edges is not mine to do.

## Whose defect this was

NoPrgress's. The byte is theirs, the Japanese ROM has Enix's value, and the
table that gives the value its meaning is untouched in both ROMs.

That distinction matters, because the Tactics-equip hang in this same patch
looks similar and is not the same thing at all. That one is Enix's code,
byte-identical in both ROMs, and only English data drives it into failing. This
one is a straight regression: the English ROM has a different byte and behaves
differently because of it.

## Checking it

```
python build.py "DQ6 NoPrgress.sfc" candidates-en.txt nametable-en.txt out.sfc
```

`build.py` prints the substitution as it applies it and refuses to write if
`$C3:49D4` does not hold `0x16` going in. The finished build is
`CRC32 5AE41C1D`.

On a screen, which is the only check that means anything here: get somebody into
the caravan, start a battle, choose Fight and a spell that targets an ally, and
count the names offered. No caravan members appear, and the window reads
correctly. Confirmed in play.
