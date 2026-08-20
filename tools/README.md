# tools

The documentation in `docs/` makes claims about this ROM: how the message
script is addressed, what the writable alphabet is, how the name table
resolves, how long a line can be. These are the programs that produce those
numbers, so the claims can be checked rather than taken on trust.

Every one of them reads a ROM you supply and prints. **None of them writes
anything.** Standard-library Python 3, no dependencies, nothing to install. No
ROM is distributed here and none ever will be.

```
python tools/census.py    <rom.sfc> [option]
python tools/charset.py   <rom.sfc> [option]
python tools/nametable.py <rom.sfc> [option]
python tools/verify.py    <stock.sfc> <patched.sfc>
```

Each takes `--help`.

---

## census.py

The message script: 870 pointer-table entries, eight messages each, 6,960 IDs.

| option | what it answers |
|---|---|
| *(none)* | how many messages, how many unwritten, where they cluster |
| `--placeholders` | every message that displays its own ID |
| `--breaks` | what follows each page break |
| `--quotes` | how often their speaker-tag quote actually appears |
| `--roundtrip` | decode everything, re-encode with the ROM's own trees, rebuild the pointer table, require byte-identity |

`--roundtrip` is the gate. Nothing should be inserted into a ROM whose script
does not survive a decode and re-encode unchanged, and it passes here because
every symbol has exactly one path through the trees.

Unknown symbols render as `<XXXX>` and are counted, never as a space. A space
fallback is legal-looking output, and one hid an entire punctuation system in
this ROM for weeks.

## charset.py

The Huffman trees and the byte-to-symbol table.

| option | what it answers |
|---|---|
| *(none)* | tree root, how many symbols are encodable, which bytes share a symbol |
| `--symbols` | every encodable symbol with its code length |
| `--symbol HEX` | is this one symbol writable in this ROM |
| `--compare OTHER` | the same figures for two ROMs side by side |

Two things it exists to settle. The tree root is **patched per ROM** and is
read from the code at `$C0:2BFB`, not assumed: decoding one ROM with the
other's root produces confident garbage rather than an error. And the writable
alphabet is the **tree**, not the font, so `--symbol 634` answers whether the
music note can be written at all.

## nametable.py

The second string system: item, spell, skill, place, monster-action and menu
names, byte-encoded and `$AC`-terminated, addressed indirectly through a group
table.

| option | what it answers |
|---|---|
| *(none)* | groups, aliasing, reachable entries, and the ID rule |
| `--untranslated` | every entry that displays its own identifier |
| `--id HEX[,HEX..]` | resolve specific string IDs, the way the game does |
| `--widths [LO-HI]` | line lengths per region, measured from the ROM's own text |
| `--breaks` | check the break-code rule |
| `--dictionary` | the dictionary codes, read out of the ROM, then measured again from the break codes |
| `--check FILE` | resolve every ID in a `nametable-en.txt` and compare |

`--dictionary` is the interesting one, because it measures the same thing
twice by unrelated routes. First it reads the dictionary out of the expander at
`$C3:FB23`, whose instructions carry the lowest code, the table address and the
entry width. Then it throws that away and derives the widths again from the
break codes alone: each break code states how long the line before it is, so
each is an equation in the widths of the codes on that line, and enough carry a
single unknown for the set to fall out by substitution. 164 equations, zero
unsatisfied, zero disagreements between the two.

Neither measurement asks what the output looks like, which is the point. Seven
of the fifty codes draw a space as part of the sequence, and a code read one
character short still produces fluent English, so reading decoded text can
never find them.

`--check` is the end-to-end one: it resolves every entry a data file names and
reports any that do not display what the file says. Use it on any build.

## verify.py

Compares a patched ROM against the one it was built from, and prints the
verification the README claims.

The check that matters is the name table, and it is not a byte diff. The table
is repacked wholesale, so almost every byte in that region moves and comparing
bytes proves nothing. Instead all 2,512 string IDs are resolved the way the
game resolves them, in both ROMs, and the results are compared.

It also enforces the promise the README makes about NoPrgress's own writing.
Their messages are allowed to differ in exactly one way, the redundant marker
`$0559` being removed, and the check fails if any other symbol in any of their
messages moves. It reports the two separately, so "not one word altered" and
"how many markers were removed" are never conflated, and it confirms the symbol
is gone from the whole payload rather than from the positions someone
remembered to look at.

---

## What is not here, deliberately

Anything that decodes the Japanese ROM's text wholesale. `charset.py --compare`
and `census.py` work on a Japanese ROM and report structure and counts, which
is all that is needed to check a claim about structure. The tooling that
renders Japanese script side by side with English is a working tool and it
stays private.

There is no option that dumps the translation's finished text either. That is
NoPrgress's work and it is not this repository's to redistribute. `--id` and
`--check` resolve the entries you ask about.

---

## Reproducing the documented figures

From a directory holding the tools and a stock NoPrgress ROM:

```
python census.py    DQ6-NoPrgress.sfc
python census.py    DQ6-NoPrgress.sfc --roundtrip
python census.py    DQ6-NoPrgress.sfc --breaks
python charset.py   DQ6-NoPrgress.sfc
python nametable.py DQ6-NoPrgress.sfc
python nametable.py DQ6-NoPrgress.sfc --widths
python nametable.py DQ6-NoPrgress.sfc --dictionary
```

| claim | where | how to check |
|---|---|---|
| 870 entries, 8 each, 6,960 IDs | METHOD 1 | `census.py` |
| 869 of 869 groups end where the next begins | METHOD 1 | `census.py` |
| the round trip is byte-exact | METHOD 1 | `census.py --roundtrip` |
| 416 display their own ID, 5 display `TEXT` | README | `census.py` |
| 15 runs of 8 or more, longest 41 | README | `census.py` |
| 123 encodable symbols in English, 1,065 in Japanese | METHOD 7a | `charset.py --compare` |
| the music note cannot be written in English | METHOD 7a | `charset.py --symbol 634` |
| a page break is never followed directly by text | METHOD 9 | `census.py --breaks` |
| 4,638 page breaks, 3,646 followed by a line break | METHOD 9 | `census.py --breaks` |
| 2,512 string IDs reaching 2,048 entries | NAME-TABLE | `nametable.py` |
| 28 groups share a base with the one before | NAME-TABLE | `nametable.py` |
| the ID rule | NAME-TABLE | `nametable.py` |
| the break-code rule | NAME-TABLE | `nametable.py --breaks` |
| the seven space-carrying dictionary codes | NAME-TABLE | `nametable.py --dictionary` |
| solving a format against its own consistency | METHOD 7b | `nametable.py --dictionary` |
| the per-region line caps | NAME-TABLE | `nametable.py --widths` |
| not one word of their text altered | README | `verify.py` |
| the redundant marker removed, all 676 of it | README | `verify.py` |
| the build verification | README | `verify.py` |

---

## Two things the tools corrected

Writing them was worth it twice over, which is the argument for shipping them
rather than describing what they would have said.

**The ID rule is simpler than it was first written up, and it is exact.** An
untranslated entry's identifier is not merely *related to* the Japanese table
index. It **is that entry's own string ID**, in hex, on 348 of 348 with no
exceptions. `nametable.py` checks it. The three shift theories that preceded
the rule all came from measuring the identifier against the entry POSITION
instead, where the same numbers spread from 0 to 464 because 464 string IDs
alias onto an earlier entry.

**The dictionary should be read from the ROM, not reconstructed.** Seven of the
fifty codes draw a space as part of their sequence: `$C9` is ` a`, `$CA` is
` d`, `$CB` is ` t`, `$CC` is ` w`, `$D6` is `e `, `$F2` is `s `, `$F7` is
`t `. A decoder that reads any of them a character short still produces fluent
English, so nothing looks wrong and nothing gets questioned: `Mudo'` + `$F2` +
`Castle` renders as `Mudo'sCastle` and the missing space passes for a packing
quirk. `$F6` is `s.`, and `$C8` is not a dictionary code at all despite sitting
beside the range.

The expander's own instructions carry the lowest code, the table address and
the entry width, so none of it has to be inferred. `--dictionary` reads it that
way and then confirms it against the break codes. The encoder held short
readings for several of these during development and was corrected before
release; the two documented line-length caps that moved, 17 to 18 and 19 to 20,
moved for the same reason.

Anyone working on this ROM should take the general lesson rather than the
specific table: measure a format against its own internal consistency, and read
the tables the renderer indexes instead of rebuilding them from what the output
looks like. `docs/METHOD.md` section 7b sets that out.
