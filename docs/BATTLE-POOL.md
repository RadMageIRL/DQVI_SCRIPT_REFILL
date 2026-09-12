# The battle message pool

The third string system in DQ6, found on 2026-09-11, and the 107 messages it
still had unwritten.

This document exists because the system was missed for the whole life of this
project. Everything below was measured from the ROM. Where something is
inferred it says so.

---

## How it was found

A player reported that a confused character attacking himself produced

```
M17D Joey
M17E
```

on screen, where `Joey` was the hero's name. The shape was familiar - it is the
same identifier-instead-of-text failure this patch already fixed twice - but
neither known system could account for it.

The message script was clean: `census.py` reported 0 of 6,960 messages
displaying their own ID. The name table still had 209 entries displaying an
identifier, but reading every one of them out of the Japanese ROM by string ID
showed what they are: debug-menu labels, unnamed location slots, Enix's own
Latin identifiers, and the naming screen's reject list. None is battle text.
An alias map was built as well, since a battle-reachable ID landing on a debug
entry would have explained it: 2,512 IDs resolve onto 2,048 positions with 464
aliased, and **not one alias lands on an identifier entry**.

So the text had to be somewhere else. Scanning for a third pointer table found
one candidate, and it was hiding in the open:

```
0x015AD1   76 entries of 3 bytes, ascending
0x015BB5   the Huffman message table starts here
```

`0x015AD1 + 76 * 3 = 0x015BB5` exactly. The second table ends on the first
byte of the known one, so every tool that started at `0x015BB5` walked right
past it.

---

## The system

Read from the loader at `$C0:27CD`, which is **byte-identical in the Japanese
ROM**, so the same reader walks both.

```
$C0:27C1  LDA $5998 / LSR x3          entry  = message ID >> 3
$C0:27CD  LDA $C15AD1,X               the table, 3 bytes per entry
$C0:27D2  ADC #$DEBD                  low word of the payload base
$C0:27DE  ADC #$00F6                  bank, so the base is $F6:DEBD
$C0:27E3  STZ $A4                     bit index zero: byte aligned, not Huffman
$C0:27EA  walk $AC / $AE              skip (ID & 7) terminators
```

| | |
|---|---|
| pointer table | `$C1:5AD1`, 76 entries of 3 bytes |
| table value | the offset from `$F6:DEBD`, so entry 0 holds 0 |
| payload | `$F6:DEBD`, file `0x36DEBD` |
| shape | 8 messages per entry, **608 messages** |
| terminators | `$AC` and `$AE`, the same pair the message script uses |
| encoding | the name-table byte charset plus the ligature dictionary at `$C3:FB50` |

It is **not** Huffman-coded. `$C0:281C` is `LDA [$A0]` followed by a pointer
increment - one byte per symbol, no tree walk. That is why the two charset
sweeps recorded in `COMPLETENESS-PASS.md` did not find it: they looked for runs
of six or more plain letters, and dictionary codes and insertion codes chop
this pool into fragments shorter than that.

### The insertion codes

Read off their own finished lines, not assumed.

| code | draws | seen in |
|---|---|---|
| `$B7` | the acting character's name | `<B7> attacks.` |
| `$B8` | the target's name | `<B8> takes <BB> damage.` |
| `$B9` | him / her / it, always as `<B9>self` | `<B7> protects <B9>self.` |
| `$BA` | his / her / its | `<B7> swings <BA> tail.` |
| `$BB` | a number | `Received <BB> experience.` |
| `$B2` | a spell or skill name | `<B3> learned <B2>.` |
| `$B3` | a party member | `<B3> made level <BB>.` |
| `$B4` | a monster | `<B4> approaches.` |
| `$B5` | an item | `Found the <B5>.` |
| `$0D` `$0E` | the M and P of MP | these are control bytes, not letters |
| `$AD` | line break | |
| `$B1` `$C2` `$AF` | window control | |

`$B9` and `$BA` are the reason none of the 107 needed a gendered pronoun
written into it. The engine already had the machinery; NoPrgress used it.

---

## What was unwritten

**107 of the 608**, and they obey the same ID rule as the message script: an
unwritten message displays **its own message ID in hex** behind a `B` or `M`
prefix. All 107 match their own index exactly, which is what distinguishes a
placeholder from a line that happens to contain a number.

```
 51  $033   B033
311  $137   B137
381  $17D   M17D
382  $17E   M17E
```

They are not scattered. The bulk is the Goof-Off vocation's random actions -
the word game, the cat's cradle, the coin flip, the ball balancing, the story
that frightens the enemy - plus a cluster of status lines, the giant demon's
scripted appearance, and the wagon-full and equipment refusals.

`DQ6_v50_Build.sfc` and stock NoPrgress both carry exactly these 107, so
nothing here was introduced by this patch. They were never written.

### The pair that started it

```
$17D   <B7> swung <BA> weapon around wildly!
$17E   But the swing carried too far, and a stumble
       drove the weapon into its own wielder!
```

`$17D` carries the actor-name code, which is why it drew as `M17D Joey`. `$17E`
carries no insertion at all, so it drew bare. They are also the only `M`-prefixed
pair in the pool.

---

## Writing them

`build.py` reads `battle-en.txt`, encodes each message with the same charset and
dictionary the name table uses, and repacks the whole pool with its pointer
table rewritten.

**A message is only written over if it currently displays its own identifier.**
The check is on the bytes, not on decoded text: the identifier is letters and
digits, so no dictionary code can occur inside one, and the encoding is exact.
Anything else makes the build refuse. That is the same promise made about their
dialogue, enforced the same way.

### Space, and where the overflow went

The 107 held 825 bytes as placeholders and take 4,134 bytes as English. The
pool grew from 11,445 bytes to 14,754.

The region from `0x36DEBD` to the Huffman payload at `0x37175B` is 14,494 bytes,
so it no longer fits, and **two entries spill** to `0x3FF10B`.

Both regions were checked before a byte was written to either:

- **`0x370B72`-`0x37175B`**, the 3,049 bytes after the old pool, decode as the
  tail of the original Japanese pool - NoPrgress rewrote the pool in place and
  their shorter English never covered the end of it. It is unreachable through
  the 76-entry table, because no entry's run of eight reaches it, and no
  long-addressing opcode anywhere in the ROM refers into it.
- **`0x3FF10B`-`0x400000`**, 3,829 bytes of `$FF` running to the last byte of
  the image, is the ROM's own tail padding, with no long-addressing opcode
  referring into it either. The spill uses 396 bytes of it.

The SNES vectors are not at risk: this is a HiROM image and the vectors are read
from bank `$C0`, at file offset `0xFFE0`, not from the end of the file.

---

## Checking it

```
python tools/census.py <rom.sfc> --battle
python tools/verify.py <stock.sfc> <built.sfc>
```

`census.py --battle` reports the pool and lists every message displaying its own
ID: **107 against a stock ROM, 0 against the release**.

`verify.py` adds three checks, and both of the ones that can fail were mutation
tested rather than just observed passing:

- the pool reads as 608 messages in both ROMs
- no message displays its own ID - **fails against v5.0**, which still has 107
- not one message of theirs changed - **fails against a build with a single
  bit flipped inside `<B7> attacks.`**

---

## What is still not known

- **`$81`.** Their own battle text writes `!` as byte `$81`, including in Dark
  Dream's dialogue, and the 107 written here follow them. Whether `$81` draws an
  exclamation mark or an ellipsis is the open question recorded elsewhere in
  this project; it is not settled by this work, and whatever the answer is, this
  pool is now consistent with their usage either way.
- **The pool has never been read on screen in English beyond the lines
  NoPrgress already wrote.** These are structural checks. The Goof-Off actions
  fire at random, several of the 107 are multi-page, and a line that encodes
  correctly can still overrun a window. Play it.
