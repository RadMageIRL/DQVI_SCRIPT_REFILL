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

## What this does not do

- **It does not fix the unbounded word-wrap fill** the translation carries. That
  is documented in the menu-fix repository and remains an open defect.
- **It does not touch item, spell, monster, place or menu strings.** Those are a
  separate system and were not censused. Anything untranslated there is
  untouched.
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
