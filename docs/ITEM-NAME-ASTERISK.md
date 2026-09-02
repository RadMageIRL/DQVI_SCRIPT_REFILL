# The trailing asterisk on five item names

`Demon Hammer*` overruns the item window. This is what the asterisk turned out
to be, what was checked before touching it, and which entries were left alone.

**Everything here was measured against the two ROMs.** Nothing is inferred from
what the names look like.

---

## 1. It is in the data, not the renderer

The asterisk is the last byte of the name-table entry, `$89`, the charset's
asterisk. It is not appended at draw time and it is not a flag the renderer
turns into a mark:

```
$084B   13 46 4E EA 01 17 CE 4E DA 89      Demon Hammer*
$0845   13 46 4E EA 01 12 4D 42 58 89      Demon Claw*
$086B   1C 4A 53 F1 53 01 10 53 4E EC 89   Mirror Armor*
$088A   15 4D CE D6 22 49 4A 46 4D 45 89   Flame Shield*
$08AB   1C 46 F8 EC E1 46 99 10 53 4E 43 CF 45 89   Meteorite|Armband*
```

That was the first thing checked, because this project has been caught the
other way round before: the speech marker `$0559` was removed on the assumption
that it drew what appeared on screen, and it took three attempts to establish
that the engine draws a mark of its own in every speech box. See METHOD 9. Here
the byte is in the string and there is no engine mark to confuse it with.

## 2. It is NoPrgress's, not Enix's

The Japanese name table is at the **same address**. The constant that reaches
it, `ADC #$8703` / `ADC #$FB` at `$C0:319C`, is byte-identical in both ROMs, so
the same group table and the same `$AC`-terminated packing read both.

```
                                entries ending on $89
Japanese  33304519                       1
NoPrgress B545C548                      14
```

The one in the Japanese ROM is `$0073`, an entry that is nothing but the
asterisk glyph itself. It is left alone here. The other thirteen are theirs.

The Japanese entries behind the five item names carry no such byte:

```
$084B   JP  2E CF 3D 28 15 24 D5 20        EN  13 46 4E EA 01 17 CE 4E DA 89
$0845   JP  10 17 2E 28 53 63              EN  13 46 4E EA 01 12 4D 42 58 89
```

## 3. It marks nothing

The item table is 255 records of 26 bytes at `$C4:0057`, and each record names
its item by string ID. Six records carry one of the five starred names, because
`Flame Shield*` has two records. Every record was compared with those six:

- **field by field**: no byte offset separates the six from the other 249
- **bit by bit**: all 192 flag bits outside the name ID were tested, and the
  rarest bit set in all six is also set in 174 of the other 249
- **by message ID**: the first hypothesis was that the five shared a
  description line. They share `$168F`, and so do 245 of the 255 records,
  because it is the default that fills an unused description slot. That
  hypothesis was wrong and is recorded here because it was convincing

So it is not a curse marker, not a "cannot be unequipped" marker, not a "usable
in battle" marker, and not tied to any message the record points at. **Nothing
in the game distinguishes these five items from any other.**

## 4. What it does do is overrun

Measured across all 218 distinct item names in the table:

| width | names |
|---:|---:|
| 11 cells | 37 |
| **12 cells** | **36** |
| 13 cells | 3 |

**Twelve is the cap the whole item table keeps to, and the only three names
above it are starred ones.**

| entry | shipped | cells | trimmed | cells |
|---|---|---:|---|---:|
| `$084B` | `Demon Hammer*` | 13 | `Demon Hammer` | 12 |
| `$086B` | `Mirror Armor*` | 13 | `Mirror Armor` | 12 |
| `$088A` | `Flame Shield*` | 13 | `Flame Shield` | 12 |
| `$0845` | `Demon Claw*` | 11 | `Demon Claw` | 10 |
| `$08AB` | `Meteorite\|Armband*` | 9 + 8 | `Meteorite\|Armband` | 9 + 7 |

Each of the three is over by exactly the asterisk, and dropping it lands each
at 12, which is their own limit rather than one imposed on them.

## 5. What was changed, and what was not

**All five item names are trimmed**, not only the three that overrun. Two items
keeping a mark that means nothing while three lose it is a worse table than
either, and the two that do not overrun are the same artifact in the same list.

**The other eight entries ending on `$89` are not touched.** None is an item,
and none overruns its own block:

| entry | | widest name in its block |
|---|---|---|
| `$02B1` | `Ocean King*` (11) | 16, `Tower of Mirrors` |
| `$02C5` | `Magiwyvern*` (11) | 16 |
| `$02DD` | `Prison Guard 2*` (15) | 16 |
| `$02F7` | `Metal Slime*` (12) | 16 |
| `$031F` | `Master*` (7) | 16 |
| `$0902` | `Without*` (8) | 12, `Battlemaster` |
| `$0903` | `Without*` (8) | 12 |
| `$0904` | `Self*` (5) | 12 |

Whether those should go too is a separate question with a separate answer, and
it has not been asked. **They are theirs and they stay** until it is.

`$0073`, the standalone asterisk, is in both ROMs and is left alone.

The prefix asterisks on entries like `*751` are a different thing entirely:
they are the identifier convention on entries the translation never wrote, and
they are covered by the ID rule in [`NAME-TABLE.md`](NAME-TABLE.md).

## 6. How it is applied, and how it is checked

One byte is dropped from the end of their own entry. The entry is not
re-encoded, for the reason METHOD 14a records: re-encoding rewrites bytes that
have nothing to do with the change. Punctuation, the break code and every
letter survive exactly as shipped. The break code in `Meteorite\|Armband*`
counts the characters on line **one**, so a byte removed from the end of line
two cannot move it.

`tools/verify.py` checks each trimmed entry against its own stock entry byte
for byte, requires exactly the one `$89` to be gone, and fails if any other
entry in the table loses one. That check was mutation-tested against v4.0,
which still carries all five, and it fails there as it should.

## 7. Reproducing this

```
tools/nametable.py <rom>            resolves every entry the way the game does
```

The item table walks from `0x040057` in 26-byte records; record +0..1 is the
name's string ID. The width figures are the length of the longest line of each
resolved name, `|` marking a break code.
