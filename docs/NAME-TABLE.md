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
entry's own string ID, in hex**. `M0C7` is string ID `$00C7`, so the Japanese it
was meant to carry is whatever string ID `$00C7` resolves to in the Japanese
ROM: entry 199, `コマンド`. Nothing has to be inferred.

Measured across the whole table, that holds on **348 of 348** with no
exceptions. `tools/nametable.py` checks it. The entries that do not resolve are
exactly the 45 whose prefix is not `M` or `*`.

This replaced three earlier theories - a constant `+2`, then `+37`, then a
"stepping" shift - and it is worth being precise about why they arose, because
the mistake is easy to repeat. All three measured the identifier against the
entry POSITION rather than the string ID. Those two part company because 464
string IDs alias onto an earlier entry, so identifier-minus-position spreads
from -531 to +464 and any shift fitted before the first collapse holds for a
while and then stops. **If a constant shift seems to work, that is the failure
mode.** Each of the three had been
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

**Three dictionary codes draw a space.** `$CB` is ` t`, `$F2` is `s `, `$F7`
is `t `. Read as `t`, `s` and `t` they still produce fluent English, so nothing
looks wrong: `Mudo'` + `$F2` + `Castle` reads as `Mudo'sCastle` and the missing
space passes for a packing quirk rather than a decoding error.

The break codes settle it with no appeal to what the codes look like. Each one
states the length of the line before it, so each is an equation in the displayed
lengths of the codes on that line, and enough of them carry a single unknown for
the whole set to fall out by substitution. Solved that way, 158 equations are
satisfied and none are left over, and every break code in the table is
consistent. `tools/nametable.py --ligatures` does it.

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
until the dictionary codes below were measured properly; a decoder that drops
their spaces measures every affected line one character short.

Longer names are split across two lines with a break code rather than truncated,
which is why `Entice Dance` is stored as `Entice` + `$96` + `Dance`.

## Verification

Because the table is repacked wholesale, the check that matters is not a byte
diff but a behavioural one: **every one of the 2,512 string IDs is resolved the
way the game resolves it, in both the before and after ROMs, and compared.**
178 changed to the intended text, 2,334 were untouched, none were wrong.

`tools/verify.py <stock> <patched>` runs that comparison, and
`tools/nametable.py <patched> --check nametable-en.txt` resolves every authored
entry and reports any that do not display what the data file says.

## A defect in v1.0

That second check is the one v1.0 does not pass, and this is the honest record
of it rather than a quiet fix.

`build.py` held the shorter readings of the three space-carrying codes above,
so its encoder reached for `$CB`, `$F2` and `$F7` whenever an authored entry
needed a bare `t` or `s`. **54 of the 178 authored entries therefore draw a
spurious space.** `Battle` is stored as `B` + `at` + `$CB` + `le` and draws as
`Bat tle`; `Restore` draws as `Res tore`; `Monsters` draws with a trailing
space.

What this is not: it is not a crash, it does not touch NoPrgress's own text,
and it does not affect the message script, either crash fix, or the gold
window. Those all verify clean. The entries are correct in `nametable-en.txt`;
only the encoder is wrong.

The fix is `NT_LIGATURES` carrying the true text for those three codes, plus
skipping space-carrying codes when encoding so a bare `t` falls through to the
plain letter byte. Rebuilt that way the check reports 178 of 178, and every
break code in the table stays consistent.
