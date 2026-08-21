# The name table

Item, spell, skill, place, monster-action and menu strings live in a system
entirely separate from the Huffman message script. This describes how it works
and how the 181 authored entries were written into it.

No ROM is distributed here and none ever will be.

## The system

Byte-encoded rather than Huffman-coded, `$AC`-terminated, packed end to end
from `$FB:8703`. It holds 2,048 reachable entries addressed by 2,512 string
IDs, so some IDs alias onto the same entry.

Addressing is indirect. The routine at `$C0:315E` splits an ID as

```
group = ID >> 4        low = ID & 0x0F
```

reads a 24-bit offset from the group table at `$C1:65E7` (3 bytes per group),
adds `$FB8703` **with carry into the bank byte**, then walks `low` `$AC`
terminators forward.

Two consequences matter:

- Entries inside a group are found **positionally**, so changing the length of
  any entry moves every entry after it. Writing longer text means repacking the
  table and regenerating all 157 group offsets.
- 28 groups deliberately share a base with the group before them - collapsed
  ranges of unused IDs. That aliasing is preserved exactly.

The carry is easy to miss. Omitting it makes the pointer table look corrupt
from group 68 onward, where in fact it is fine.

## Finding the Japanese

An untranslated entry displays its own identifier, and **that identifier is the
entry's own string ID, in hex**. `M0C7` is string ID `$00C7`, so the Japanese it
was meant to carry is whatever string ID `$00C7` resolves to in the Japanese
ROM: entry 199, `コマンド`. Nothing has to be inferred.

Measured across the whole table, that holds on **348 of 348** with no
exceptions, and it was re-verified on the release build at **170 of 170** for
the entries that still show an identifier. `tools/nametable.py` checks it.

**The rule applies to the `M` and `*` prefixes only.** The 45 entries with some
other prefix do not follow it: `E01` sits at string ID `$01B1`, not `$0001`.
That does not make them unreadable, which an earlier version of this document
claimed. Resolve such an entry by **its own string ID** and the Japanese comes
out normally - `$01B1` is the Latin string `E01` in the Japanese ROM, so it is
an internal label rather than untranslated text. `D07`, `S02`-`S45`, `K02`-`K12`
and `ID001`-`ID010` are all the same. The one exception is `C030` at `$023E`,
whose Japanese is `へんしん` and which is real content.

The two lookups are easy to confuse and give different answers. Resolving an
entry by the number inside its displayed identifier, rather than by its own
string ID, points somewhere unrelated and still returns readable Japanese.

This replaced three earlier theories - a constant `+2`, then `+37`, then a
"stepping" shift - and it is worth being precise about why they arose, because
the mistake is easy to repeat. All three measured the identifier against the
entry POSITION rather than the string ID. Those two part company because 464
string IDs alias onto an earlier entry, so identifier-minus-position spreads
from -531 to +464 and any shift fitted before the first collapse holds for a
while and then stops. **If a constant shift seems to work, that is the failure
mode.** Each of the three had been verified on a handful of anchors and then
applied everywhere.

## The encoding, and four things that are not obvious

**Bytes `$0C`-`$0F` shadow the letters H, M, P and G** in the byte-to-symbol
table, but they are renderer control codes rather than glyphs - `$0D` draws a
tilde. Encoding "M" as `$0D` produces `~adante 2`. H, M, P and G must use
`$17`, `$1C`, `$1F` and `$16`.

**Bytes `$82`-`$9D` are line breaks, not spaces.** In the Japanese ROM those
same bytes are the full-width Latin alphabet; the translation collapsed them
onto one symbol and repurposed them. A break code is `0x90` plus the length of
the line before it, verified against every multi-line entry in the stock table:
`Ice`/`Breath` `$93`, `Slime`/`Behemoth` `$95`, `Octopus`/`Jar Boy` `$97`,
`Scorching`/`Breath` `$99`, `Metal King`/`Slime` `$9A`, `Moon Folding`/`Fan`
`$9C`, `Spotted Slime`/`Boss` `$9D`.

Three bytes in that range are glyphs rather than breaks: `$85` the label colon,
`$89` an asterisk, `$8B` a comma.

**Seven dictionary codes draw a space**, and the dictionary should be read
from the ROM rather than reconstructed.

Bytes at or above `$C9` are dictionary codes, each drawing a short fixed
sequence. Seven of the fifty include a space: `$C9` is ` a`, `$CA` is ` d`,
`$CB` is ` t`, `$CC` is ` w`, `$D6` is `e `, `$F2` is `s `, `$F7` is `t `.

That matters more than it sounds, because **a code read one character short
still produces fluent English**. `Mudo'` + `$F2` + `Castle` renders as
`Mudo'sCastle`, and a missing space passes for a packing quirk rather than a
decoding error. Nothing looks wrong, so nothing gets questioned. `$F6` is `s.`
and had been read as `age`; `$C8`, which sits right beside the range, is not a
dictionary code at all and appears only in four dead name-entry grid slots.

None of this needs deducing. The expander at `$C3:FB23` reads

```
CMP #$00C9        the lowest dictionary code
BCC ...           below that, not a dictionary code at all
SBC #$00C9
ASL / TAX
LDA $C3FB50,X     first byte of the pair
LDA $C3FB51,X     second byte
```

so the lowest code, the table address and the entry width are all in the
instructions, and `$FF` terminates the table. `tools/nametable.py --dictionary`
reads it that way.

It then measures the same thing a second time without looking at the table at
all. Each break code states the length of the line before it, so each is an
equation in the displayed widths of the codes on that line, and enough carry a
single unknown for the whole set to fall out by substitution. 164 equations,
158 solvable, zero unsatisfied, and **zero disagreements with the table read
out of the ROM**. Two independent measurements, neither of which asks what the
output looks like.

The encoder held the short readings during development and was corrected before
release.

**Japanese bytes `$8C`-`$A5` are the full-width Latin alphabet A-Z.** Without
this, entries decode as unmapped kanji and read as unknown when they are
trivial: `[?][?]` at IDs `$CE` and `$CF` is simply `H:` and `M:`. It also
exposed eleven editor labels - `OBJ0`-`OBJ3`, `LV0`-`LV3`, `X:`, `Y:` - which
would otherwise have been translated unnecessarily.

## Line length

Caps were measured per region against the translation's own entries rather than
assumed, and they differ sharply:

```
battle actions      9 characters a line, and not one of theirs exceeds it
skill descriptions 12
menu / status      18
place names        20
```

Reproduce with `tools/nametable.py <rom> --widths`, which also prints the block
map those four regions were read off. The last two were quoted as 17 and 19
until the dictionary codes above were measured properly: a decoder that drops
their spaces measures every affected line one character short.

Longer names are split across two lines with a break code rather than truncated,
which is why `Entice Dance` is stored as `Entice` + `$96` + `Dance`.

## Verification

Because the table is repacked wholesale, the check that matters is not a byte
diff but a behavioural one: **every one of the 2,512 string IDs is resolved the
way the game resolves it, in both the before and after ROMs, and compared.**
181 changed to the intended text, 2,331 were untouched, none were wrong.

`tools/verify.py <stock> <patched>` runs that comparison, and
`tools/nametable.py <patched> --check nametable-en.txt` resolves every authored
entry and reports any that do not display what the data file says.

