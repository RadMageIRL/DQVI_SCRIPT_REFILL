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
| `--ligatures` | solve the dictionary codes' lengths from the break codes alone |
| `--check FILE` | resolve every ID in a `nametable-en.txt` and compare |

`--ligatures` is the interesting one. Every break code states how long the line
before it is, so each break code is an equation in the displayed lengths of the
dictionary codes on that line. Enough of them have a single unknown that the
whole set falls out by substitution, and the rest then act as a check. It needs
no assumption about what any code *says*. It is the check that catches a
dictionary code whose text quietly carries a space, and it found one here (see
below).

## verify.py

Compares a patched ROM against the one it was built from, and prints the
verification the README claims.

The check that matters is the name table, and it is not a byte diff. The table
is repacked wholesale, so almost every byte in that region moves and comparing
bytes proves nothing. Instead all 2,512 string IDs are resolved the way the
game resolves them, in both ROMs, and the results are compared.

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
| the per-region line caps | NAME-TABLE | `nametable.py --widths` |
| the build verification | README | `verify.py` |

---

## Two things the tools corrected

Writing them was worth it twice over, which is the argument for shipping them
rather than describing what they would have said.

**The ID rule is simpler than `docs/NAME-TABLE.md` says, and it is exact.** An
untranslated entry's identifier is not merely *related to* the Japanese table
index. It **is that entry's own string ID**, in hex, on 348 of 348 with no
exceptions. `nametable.py` checks it. The three shift theories that preceded
the rule all came from measuring the identifier against the entry POSITION
instead, where the same numbers spread from 0 to 464 because 464 string IDs
alias onto an earlier entry.

**Three dictionary codes draw a space that a decoder can easily drop.** `$CB`
is ` t`, `$F2` is `s `, `$F7` is `t `, and a decoder that reads them as `t`,
`s` and `t` still produces fluent English, so nothing looks wrong. The break
codes settle it without any appeal to what the codes look like: run
`nametable.py --ligatures`.

That correction has a consequence, and it is recorded rather than quietly
fixed. **The v1.0 patch encodes 54 of its 178 name-table entries with a
spurious space**, because `build.py` held the shorter readings. `Battle` is
stored as `B` + `at` + `$CB` + `le` and draws as `Bat tle`. Run:

```
python nametable.py <patched.sfc> --check nametable-en.txt
```

The entries are correct in `nametable-en.txt`; only the encoder is wrong, and
the fix is three characters in `build.py`'s `NT_LIGATURES` plus skipping
space-carrying codes when encoding. It is a rendering defect, not a crash, and
nothing else in the patch is affected: the message script, both crash fixes and
the gold window all verify clean.
