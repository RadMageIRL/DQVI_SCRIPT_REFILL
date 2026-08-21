# DQ6 Script Refill

A patch that completes the untranslated messages in the **NoPrgress** English
translation of *Dragon Quest VI: Maboroshi no Daichi* for the Super Famicom,
and folds in two crash fixes.

---

## Most of this is someone else's work

**NoPrgress translated this game.** 6,539 of the 6,960 messages in the main
script are theirs. Every character voice, every place name, every item and
spell and joke you will read is theirs. This patch adds 421 messages, six
percent, and spends most of its effort trying to sound like the other
ninety-four.

**DeJap** did the foundational Dragon Quest VI translation work that this line
of hacks descends from, and their name belongs alongside NoPrgress's whenever
this translation is discussed.

Nothing here replaces, corrects or improves their translation. **Not one word
of their writing is altered**, and that is verified on every build rather than
asserted: every symbol of all 6,539 of their messages is exactly what they
shipped, with one exception that changes no wording at all: a redundant marker
symbol with no English glyph is removed wherever it appeared. See "The speech
marker" below.
Where their choices differ from
series convention, **their choices win** and this patch follows them. Luisa
rather than Ruida. Amoru. Erika. "the castle of the gods" rather than Zenithia.
The Sword of Ramias, the Shield of Sufida, the Armor of Orgo, the Helm of
Cevas. Those are their calls and this patch defers to them everywhere.

If you enjoy playing this game in English, that is largely their doing.

---

## What this patch does

The translation shipped with 421 messages never written. In play they display
as raw data where dialogue should be: 416 show their own message ID as decimal
digits, so an NPC says `3020`, and 5 show the string `TEXT` and their ID, like
`TEXT6478`. They sit between IDs 2,894 and 6,956, in the latter half of the
game, and they cluster: 15 runs of eight or more consecutive messages, the
longest 41 in a row. That is why entire locations can read as nothing but
numbers.

This patch writes those 421 messages, in English, from the Japanese original.

It also writes **182 name-table entries** - item, spell, skill, place,
monster-action and menu names the translation left showing the game's own
internal identifier, so a location read `M194` and a battle action read `M6BA`.
See "Scope" below for what was deliberately left alone and why.

It also removes a **redundant speech marker**, all 676 occurrences of the one
symbol in their script with no English glyph behind it. It drew a stray shape
wherever it appeared, always after a marker the engine had already drawn. See
"The speech marker" below.

It also includes both crash fixes from
[DQVI_NOPRGRESS_MENU_FIX](https://github.com/RadMageIRL/DQVI_NOPRGRESS_MENU_FIX):
the **Info > All** crash and the **Forget** crash. You do not need to apply that
patch as well. This one contains it.

- **Info > All** hangs if you back out before the screen finishes drawing. A
  three-byte `STA $3AC2` was deleted from `$C3:3538`, so the party-slot loop
  bound keeps a stale `$FF` sentinel and the loop runs past the end of the
  party. Fixed by restoring 87 bytes from the Japanese ROM.
- **Forget** crashes because of a memory allocation collision, not a logic bug:
  the translation put word-wrap state inside a block the original game clears
  wholesale. Fixed by relocating three variables across 19 sites, operands
  only. **Keep savestates the first time you use Forget.**

[`docs/CRASH-FIXES.md`](docs/CRASH-FIXES.md) has the detail, including what
these fixes deliberately do not do.

And it restores the **gold window on the info screen**, which the translation
lost. See below.

## The speech marker

The engine draws the opening mark on NPC dialogue itself: a star and a bracket
before the first word, the same thing the Japanese original draws. It does this
in every box that carries speech, ordinary villagers and shop clerks alike.

NoPrgress additionally wrote symbol `$0559` into the script **676 times**.
`$0559` is the one symbol in their script with no English glyph behind it, so
everywhere it appears it drew a stray two-part mark, and everywhere it appears
the engine had already drawn the real one.

```
before   * : <stray>Welcome to Amoru, town of water.
after    * : Welcome to Amoru, town of water.
```

It is removed outright rather than replaced, in every position: 534 opening a
message, 115 after the opening quote inside a tagged line, 25 after a context
control code, and 2 in the trailing filler past the last real message. What is
left is the engine's own marker.

**No wording changes.** The symbol carried no word, and the build fails if any
other symbol in any of their messages moves.

## The gold window

Open the info screen in the Japanese game and your gold is in the top right.
Open it in the English translation and it is not there at all.

**What happened.** English stat labels are wider than Japanese ones, so the
status window was widened to fit them. That left the gold window with nowhere to
sit:

```
Japanese   status cols 10-21   gold cols 22-30    side by side
English    status cols 10-24   gold cols 16-23    gold underneath the status window
```

Having no room for it, the translation deleted the call that draws the gold
figure - seven bytes - and padded the gap so the surrounding code still lined
up. The same technique appears four bytes earlier in the deletion that causes
the Info > All crash, so the two were almost certainly done in the same sitting.

**What this patch does.** It moves the gold window to the top left, where the
English layout has room, and puts the draw call back. The window draws the same
one-byte `G` string that the translation's *other* gold window already uses -
their own substitution, applied to the one place they did not apply it.

Nothing else moves. Only the gold window's own descriptor changes; the status
window, the command menu and every other window are byte-identical to the ones
NoPrgress shipped.

**This restores original behaviour rather than adding anything.** The gold
window is the game's, not ours. It was in Dragon Quest VI in 1995 and it is
back.

## Applying it

**This is what you want if you just want to play.** One step, no Python.

**One patch contains everything** - the 421 messages, the 182 names, both crash
fixes and the gold window. There is nothing else to apply and no order to get
right. Do not apply the menu-fix patch as well; this one already contains it.

You need a **headerless** NoPrgress-translated ROM. Check it first:

```
source   CRC32 B545C548
```

Then apply `DQ6-SFC-NoPrgress-RM-ScriptRefill.bps` with
[Flips](https://www.romhacking.net/utilities/1040/) or any equivalent.

**With the Flips window:** click *Apply Patch*, choose the `.bps`, then choose
your ROM. It writes the patched copy beside it. Your original is not modified.

**From a command line:**

```
flips --apply DQ6-SFC-NoPrgress-RM-ScriptRefill.bps "DQ6 NoPrgress.sfc" "DQ6 Refill.sfc"
```

![Applying the patch in an empty directory holding only the ROM and the .bps: flips reports the patch was applied successfully, a new DQ6 Refill.sfc appears, and its SHA-1 is shown](screenshots/apply-run.png)

**Without Flips at all**, if you have Python: `patchRM.py` applies the same
`.bps` and needs nothing installed. Put it beside the patch and your ROM.

```
python patchRM.py "DQ6 NoPrgress.sfc"
```

![patchRM.py run from a Windows command prompt in a folder holding only the ROM, the .bps and the script: it prints the patch and source CRC32s, writes DQ6 NoPrgress (Script Refill).sfc, and reports all checksums verified](screenshots/patchRM-run.png)

It checks the patch's own CRC32, refuses a wrong or already-patched ROM, and
verifies the output before telling you it worked. Standard-library Python 3, no
dependencies.

Check what you get, whichever route you used:

```
result   CRC32 0B83A063   SHA-1 4d2d98cb48c353c54a8d0d5490f114ad9e8ded43
```

That is the whole thing. **You are done** - the 421 messages, the 182 names,
both crash fixes and the gold window are all in that one output file.

If the CRC32 does not match, your source ROM is not the one this targets. BPS
records its expected source, so Flips will normally refuse a wrong ROM rather
than producing a broken one - that is why the `.bps` is preferred.

The `.ips` is the same patch in an older format, for tools that cannot read BPS.
**IPS cannot check its input at all**: it will apply to anything and report
success. Use it only if you have to, and check the hash afterwards.

## Building it yourself

**You do not need this to play - the section above is the whole job.** This is
here so the patch does not have to be taken on trust: `build.py` rebuilds the released ROM from the English text in
this repository, so anyone can check that what the patch writes is what these
files say it writes, and get the same hash.

That is also why `candidates-en.txt` and `nametable-en.txt` are published. Every
authored line is readable text rather than something buried in a binary diff.

The patch is reproducible from this repository alone. `build.py` performs every
step - both crash fixes, the gold window, the name table and the message script
- so a stock NoPrgress ROM plus the two text files here reproduces the released
ROM byte for byte. Standard-library Python, no dependencies, and nothing is
fetched from anywhere else.

```
python build.py DQ6-NoPrgress.sfc candidates-en.txt nametable-en.txt DQ6-Refill.sfc
```

![The build script running: it reports the source ROM as CRC32 B545C548, applies both crash fixes across 21 sites, restores the gold window, writes the name-table entries, decodes 6,960 messages, substitutes 421, and reports the finished ROM's CRC32 and SHA-1](screenshots/build-run.png)

If your output is not `0B83A063`, the input ROM is not the one this targets.
Check its CRC32 before anything else.

The script refuses to write if the ROM is not what it expects. Every fix checks
its own site first - the crash-fix span, all 21 Forget relocation sites, and the
gold routine - so pointing it at the wrong ROM fails loudly rather than
producing something broken.

## How the 421 messages and 182 names were written

From the Japanese script and from NoPrgress's own English, and from nothing
else. No later official localization was consulted at any point, including for
checking. Where a term had no precedent in their text, the earlier NES-era
Dragon Warrior convention was used, being earlier rather than later.

Their finished 6,539 messages were treated as the specification. Names came
from their spellings. Vocabulary came from their choices. Layout limits were
measured from their pages rather than guessed, and so was voice: their habit of
breaking a sentence with an exclamation mark where the Japanese hesitates, for
instance, is reproduced at the rate they use it and in the places they use it.

The name-table entries were held to the same rule, which repeatedly overrode
what read better in isolation. `ゆうわくおどり` is `Entice Dance` because that is
their existing rendering; `かみのふね` is `Ship of the Gods` because their text
already fixes `神の` as "of the gods"; `てきぜんたい` is `Enemies`, not
`All Enemies`, because that is how they render it elsewhere. Line lengths were
measured per region against their own entries rather than assumed - the caps
differ, from 9 characters a line for battle actions to 20 for place names.

[`docs/METHOD.md`](docs/METHOD.md) describes the approach in full, including the
parts that went wrong, and is written so it can be followed for a different SNES
translation.

## Checking any of this

The claims above are measurements, so [`tools/`](tools/) holds the programs that
produce them. Each reads a ROM you supply and prints; none of them writes
anything, and there are no dependencies.

```
python tools/census.py    DQ6-NoPrgress.sfc            # 870 x 8 = 6,960 messages, 421 unwritten
python tools/census.py    DQ6-NoPrgress.sfc --roundtrip  # the byte-exact re-encode gate
python tools/charset.py   DQ6-NoPrgress.sfc            # the trees, and what can be written at all
python tools/nametable.py DQ6-NoPrgress.sfc            # the name table and the ID rule
python tools/verify.py    DQ6-NoPrgress.sfc DQ6-Refill.sfc
```

[`tools/README.md`](tools/README.md) maps each documented figure to the command
that reproduces it. Writing them corrected two things in the documentation,
both recorded there.

## Scope: what is complete and what is not

**The message script is complete.** All 421 untranslated messages are written,
which is every one in the 6,960-message dialogue system. That is verified on the
built ROM rather than asserted: it is decoded back out and checked for both
known placeholder forms, and the result is zero of each.

**The name table is done too.** Item, spell, skill, place, monster-action and
menu names are a separate system from the message script: byte-encoded rather
than Huffman-coded, stored in different tables, reached a different way. It had
never been censused before this project.

**In the stock ROM, 394 entries displayed the game's own internal identifier**,
so a location read `M194` and a battle action read `M6BA`. **182 are now
written, leaving 212 in the release build.** Every figure here was measured
against a ROM, and each says which ROM it describes:

| | stock `B545C548` | release `0B83A063` |
|---|---|---|
| entries displaying an identifier | **394** | **212** |
| written by this patch | - | **182** |

`tools/nametable.py --untranslated` reports 393 and 211. It matches a
single-letter prefix only, so it does not count `ID001`-`ID010` or `DS29`. The
difference between the two ROMs, 182, is the same either way.

### What the remaining 212 are

Established by reading the Japanese behind every one of them, resolved by the
entry's own string ID out of the Japanese ROM:

| | count | |
|---|---|---|
| naming-screen rejection list | **75** | compared against what you type, never drawn |
| internal labels | **62** | the Japanese is itself a Latin identifier |
| debug and editor labels | **70** | written in Japanese, unreachable in normal play |
| **genuinely unresolved** | **4** | see below |

**Not one of the first 207 can appear in normal play.**

The **75** are the words the naming screen refuses. Translating them would mean
authoring a list of English obscenities into a ROM, which is a content decision
rather than a translation, and it would change nothing.

The **62** were never translatable text at all, because the Japanese original
holds the same Latin string: `EDIT`, `RESIZE`, `MOVE`, `MAP`, `OBJ0`-`OBJ3`,
`LV0`-`LV3`, `X:`, `Y:`, `C01SHIPR`, `HP MP MAX`, and the `E01`, `D07`,
`S02`-`S45`, `K02`-`K12`, `ID001`-`ID010` slots. Several only read as garbage
because bytes `$0C`-`$0E` shadow H, M and P.

The **70** are map-editor and debug-menu labels: map tile attributes, castle map
slots, a debug menu with cheat-Zoom and a sound test, and a window debug block.
**These were missed for months because they are written in Japanese**, and the
search had been for Latin identifiers like `OBJ0`. Internal strings are not
required to be in the developer's second language.

Eleven of the Latin labels were only identifiable after working out that
Japanese bytes `$8C`-`$A5` are the full-width Latin alphabet. Before that they
decoded as unmapped kanji and looked like ordinary text. Without that find they
would have been translated unnecessarily, and three map slots would have been
given invented names.

### The 4 that are not settled

Every entry in the table can now be read. An earlier version of this file said
that four entries whose prefix is not `M` or `*` could not be resolved at all,
naming `E01`, `D07` and `C030`. That was wrong on all three. `E01` and `D07`
resolve to the Latin strings `E01` and `D07` in the Japanese ROM and are
internal labels rather than content. `C030` resolved to a real word and **is now
written**: it is the `Transform` entry in the monster-name block, matching the
translation's own rendering of the same Japanese elsewhere in the table. Whether
any encounter references that slot was not confirmed; writing it costs nothing
if it is unused.

What remains unresolved is a question of meaning, not of access:

| shows | Japanese | why it is left alone |
|---|---|---|
| `*70A` | `そうぞうを` | **the reading is settled**: the next entry is `ぜっする`, and 想像を絶する is fixed, so it is "imagination". The English is what is blocked, because they render `ぜっする` as `Really` and a faithful fragment collides with it. |
| `M14E` | `かみ` | god, hair or paper. **The table itself uses `かみ` both ways**: 神 four times (`かみのふね`, `かみのいかり`) and 髪 twice (`かみをかきあげる`, `ぎんのかみかざり`). No bare 神 exists anywhere in the table to take a wording from, and this entry sits near none of the seven. |
| `M14D` | `ばか` | "idiot". The four forms of address two entries away are all kinship terms with `ちゃん`, three with `たち`; this shares none of that, so the group does not claim it. |
| `M11C` | `がた` | an honorific pluralizing suffix. They spend their one English pluralizer, `s`, on `たち` at `$0118`, and English has no honorific plural. |

**`M6EB デュランのもと` is written as `Off to|Duran`, and it is marked INFERRED.**
It is the one entry here written without a precedent for its head noun, so the
reasoning is recorded rather than assumed. `〜のもと` after a proper noun is the
ordinary locative, the `〜のもとで働く` sense, "at X's side"; the `素` reading,
which would give something like `Duran Mix`, wants a substance rather than a
person. It sits in the Goof-off random-action pool at slot 39 of 56, and the
pool's humour is things that make no situational sense - `Playing House`,
`Fake Blast`, `Solo Hand Game` - so a Goof-off wandering off to the demon lord
mid-battle is that joke. The ability table gives it a record at index 390, so it
IS selectable and a player will see it, which is what decided the trade: an
identifier on screen is certainly wrong, and a reasoned guess in the right
register is probably right.

Alternatives considered and recorded: `Duran's Side` (accurate, reads flat),
`Follow Duran` (good register, but see below), `Duran Mix` (the `素` reading the
proper noun argues against).

**`Follow Suit` was ruled out and that is worth keeping.** It had been suggested
that this entry might be the ability a later remake calls Follow Suit. It is
not. Follow Suit is `まねまね`, which is `$065D` in this table and which the
translation already renders as `Repeat`. It also sits in the battle-actions
region rather than the Goof-off pool, because it is a rank-learned ability and
the 56 are random actions - two different categories.

**`M6FD し` was reclassified, not translated.** It is not a Goof-off action at
all. The ability table at `0x08C674` holds 25-byte records that each begin with
their name's string ID, and the Goof-off run is records 351-407, IDs
`$06C4`-`$06FC`: the command label plus **56 actions**, contiguous, bounded by
null records at either end. **No record anywhere in that table carries `$06FD`.**
It is a name-table slot with nothing selecting it, so it belongs with the
internal entries rather than with untranslated content. `$06EB`, by contrast,
does have a record, at index 390, so it is a real selectable action.

**Two were resolved after this list was first written.** `M427`, `におうふくろ`,
is now `Stink Bag`: it sits immediately past a hard structural boundary - the
vocation rank ladders run 919 to 1062, exactly 18 groups of 8 - and is paired
there with `メガンテがかかるうでわ`, the only other modifier-plus-common-noun
entry nearby. That makes it a descriptive label rather than a name, and "the bag
that smells" parses as a description where 仁王袋 does not. The `におう` reading
is inferred.

`M0F5`, `ひき`, is the animal counter, and it is now **blank rather than
translated**. That is the translation's own convention for a string English does
not express: 75 of their entries are empty where the Japanese has content, none
of the Japanese entries are empty, and their `$0324` is the counter for flat
objects, which they blanked. `tools/verify.py` asserts it stays empty.

One small thing suggests these gaps are not arbitrary. The Goof-off block runs
50 entries, and the translation wrote 48 of them. The two they left are
`デュランのもと` and `し` - which are also the only two that break the block's
construction, the one `[X]の[Y]` naming a character and the one bare kana. Weak
evidence, and it proves nothing on its own, but whatever stopped them there is
probably what stops anyone.

Every one of them is left showing its identifier. **A gap is better than a
confident wrong answer**, and inventing a reading for a two-kana entry is
exactly how a translation acquires errors that nobody can later trace.

## What else this does not do

- **It does not fix the unbounded word-wrap fill** the translation carries. The
  Forget fix moves that buffer out of harm's way and gives it 200 bytes of
  headroom against a 136-byte worst case, but it does not bound the fill. That
  remains an open defect. See [`docs/CRASH-FIXES.md`](docs/CRASH-FIXES.md).
- **It does not touch a word of NoPrgress's own text.** Every symbol of their
  6,539 messages is what they shipped, apart from a redundant marker symbol
  removed wherever it appeared, which carried no word. The build fails if any
  other symbol in any of their messages moves.
- **It does not claim to be complete or correct.** 421 messages and 182 names
  were authored by someone who is not a professional translator, checked against
  a corpus rather than against a native speaker. Errors are mine. Reports are
  welcome.

## Credits

- **NoPrgress** - the English translation. Nearly all of the text you will read.
- **DeJap** - the foundational Dragon Quest VI translation work this descends from.
- **Enix** - *Dragon Quest VI: Maboroshi no Daichi*, 1995.
- The **RetroGameTalk** user whose report first established that the missing
  messages were dialogue rather than menu strings, which is what started this.

## Licence

The tooling and the authored English in this repository are MIT licensed. That
covers this repository's contents only. It does not extend to the game, to the
NoPrgress translation, or to any ROM.

No ROM is distributed here and none ever will be.
