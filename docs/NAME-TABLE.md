# The name table

Item, spell, skill, place, monster-action and menu strings live in a system
entirely separate from the Huffman message script. This describes how it works
and how the 178 authored entries were written into it.

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
entry's index in the Japanese table**. `M0C7` is Japanese entry `0xC7` = 199,
`コマンド`. Verified on three independent anchors and then across the whole
table: of 370 untranslated entries, 325 resolve, and the 45 that do not are
exactly those whose prefix is not `M` or `*`.

This replaced three earlier theories - a constant `+2`, then `+37`, then a
"stepping" shift. Measured against the ID rule, ID-minus-position ranges from
-531 to +464, so no constant shift exists anywhere. Each of the three had been
verified on a handful of anchors and then applied everywhere.

## The encoding, and three things that are not obvious

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
menu / status      17
place names        19
```

Longer names are split across two lines with a break code rather than truncated,
which is why `Entice Dance` is stored as `Entice` + `$96` + `Dance`.

## Verification

Because the table is repacked wholesale, the check that matters is not a byte
diff but a behavioural one: **every one of the 2,512 string IDs is resolved the
way the game resolves it, in both the before and after ROMs, and compared.**
178 changed to the intended text, 2,334 were untouched, none were wrong.
