# DQ6 Script Refill

A patch that completes the untranslated messages in the **NoPrgress** English
translation of *Dragon Quest VI: Maboroshi no Daichi* for the Super Famicom,
and folds in two crash fixes.

---

## This is somebody else's work, and almost all of it

**NoPrgress translated this game.** 6,539 of the 6,960 messages in the main
script are theirs. Every character voice, every place name, every item and
spell and joke you will read is theirs. This patch adds 421 messages, six
percent, and spends most of its effort trying to sound like the other
ninety-four.

**DeJap** did the foundational Dragon Quest VI translation work that this line
of hacks descends from, and their name belongs alongside NoPrgress's whenever
this translation is discussed.

Nothing here replaces, corrects or improves their translation. Their text is
untouched: all 6,539 of their messages are byte-identical to the ones they
shipped, and that is verified on every build. Where their choices differ from
series convention, **their choices win** and this patch follows them. Luisa
rather than Ruida. Amoru. Erika. "the castle of the gods" rather than Zenithia.
The Sword of Ramias, the Shield of Sufida, the Armor of Orgo, the Helm of
Cevas. Those are their calls and this patch defers to them everywhere.

If you enjoy playing this game in English, that is their doing. Please go and
say so to them, not to me.

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

It also includes both crash fixes from
[DQVI_NOPRGRESS_MENU_FIX](https://github.com/RadMageIRL/DQVI_NOPRGRESS_MENU_FIX):
the **Info > All** crash and the **Forget** crash. You do not need to apply that
patch as well. This one contains it.

## Applying it

Patch a **headerless** NoPrgress-translated ROM.

```
source   CRC32 B545C548
result   CRC32 6D941CBF   SHA-1 bbae5bfae769aba8a3c2edd9c6eeda9a47f55f6d
```

`DQ6-SFC-NoPrgress-RM-ScriptRefill.bps` is preferred. The `.ips` is provided for
tools that cannot read BPS. Use [Flips](https://www.romhacking.net/utilities/1040/)
or any equivalent.

## How the 421 were written

From the Japanese script and from NoPrgress's own English, and from nothing
else. No later official localization was consulted at any point, including for
checking. Where a term had no precedent in their text, the earlier NES-era
Dragon Warrior convention was used, being earlier rather than later.

Their finished 6,539 messages were treated as the specification. Names came
from their spellings. Vocabulary came from their choices. Layout limits were
measured from their pages rather than guessed, and so was voice: their habit of
breaking a sentence with an exclamation mark where the Japanese hesitates, for
instance, is reproduced at the rate they use it and in the places they use it.

[`docs/METHOD.md`](docs/METHOD.md) describes the approach in full, including the
parts that went wrong, and is written so it can be followed for a different SNES
translation.

## Scope: what is complete and what is not

**The message script is complete.** All 421 untranslated messages are written,
which is every one in the 6,960-message dialogue system. That is verified on the
built ROM rather than asserted: it is decoded back out and checked for both
known placeholder forms, and the result is zero of each.

**The name table is not, and this patch does not touch it.** Item, spell,
monster, place and menu names are a separate system: byte-encoded rather than
Huffman-coded, stored in different tables, reached a different way. It was
censused for the first time in this project, and **298 of its 1,779 entries are
untranslated**. They display as the game's own internal identifiers, so a place
name can read `M194` where a location name belongs. **46 of those sit in the
place-name block**, beside towns you will visit.

Two things are worth knowing about that:

- **None of it can display as Japanese.** The English character table remaps
  every kana slot to a blank, and no entry carries one anyway. There is no path
  by which a Japanese item or place name reaches the screen.
- **It predates this patch entirely.** All 298 were untranslated before the
  refill and are untouched by it. Nothing here made it worse.

Whether a given one is ever reachable on screen is not established. Many map
slots are interiors that never display a name at all, so the visible count may
be well below 46.

Finishing them is a possible second phase and a harder job than the 421 in one
respect: most have no parallel English anywhere in the ROM to mine for the
translators' vocabulary, and place names have to agree with the geography rather
than just read well.

## What else this does not do

- **It does not fix the unbounded word-wrap fill** the translation carries. That
  is documented in the menu-fix repository and remains an open defect.
- **It does not claim to be complete or correct.** 421 messages were authored by
  someone who is not a professional translator, checked against a corpus rather
  than against a native speaker. Errors are mine. Reports are welcome.

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
