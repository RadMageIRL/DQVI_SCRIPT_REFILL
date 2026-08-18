# Completing an unfinished SNES fan translation from its own ROMs: method

The method document for the DQ6 NoPrgress script-refill project, generalized so
that someone attempting the same job on another SNES translation can follow the
approach without access to the original working session.

The situation this method addresses: a fan translation shipped incomplete, the
original translators are gone, their tools are gone, and the only artifacts are
the patched ROM and the original Japanese ROM. The goal is to author the missing
text faithfully, in the original translators' voice, without consulting any
official localization.

The single organizing principle, learned the hard way: **measure what the game
displays, never what the bytes are** - and when a measurement and an inference
disagree, the measurement wins.

---

## 1. The message system must be decoded from its own code

Do not trust any published notes about the text format; read the reader.
For DQ6 the routine at `$C0:2B69` revealed:

- A pointer table (870 x 3 bytes at `$C1:5BB5`) indexed by **`ID >> 3`**, not by
  ID: each entry heads a run of 8 messages split by terminator symbols. Getting
  this wrong by a factor of 8 was this project's founding error - a census
  counted 870 "messages" that were actually 6,960.
- Huffman text: two node tables (bit-clear / bit-set), byte-indexed 16-bit
  nodes, MSB-first, bit 15 = internal. **The tree root is patched per ROM**
  (read it from the code, `$C0:2BFB` here): using the English root on the
  Japanese ROM produces confident garbage, not an error.
- The payload end is unconstrained by the table: the final group's tail can
  absorb trailing filler. Validate every group ends where the next begins
  (869/869 here), and treat the last group's tail with suspicion - real content
  ended at ID 6956 of 6960, and 6957-6959 decoded both ROMs to garbage.

**Gate everything on a byte-exact round trip** before planning any insertion:
decode all messages, re-encode with the existing trees, rebuild the pointer
table, and require byte-identity with the original. Here the encode is
deterministic because every symbol has exactly one tree path; verify that
rather than assuming it.

## 2. Finding what is untranslated: decode, do not diff

Byte-diffing the two ROMs at equal offsets is worthless for text: a rebuilt
payload shifts every message. Worse, statistical tests measure the wrong thing.
This project's placeholders **display their own message ID in decimal digits**,
which passes both "is it Latin?" (digits are Latin) and "did the bytes change?"
(substitution is change). The reliable test was structural: a message whose
leading digits spell exactly its own ID, at 416 of 416 with zero false
positives.

## 3. Building the glyph map without the font

The Japanese font never existed anywhere as a bitmap (this engine composes
glyphs generatively at draw time), so the map came from three sources, kept in
two strictly separate tiers.

### 3a. Kana: the ROM's own name-entry table

Both ROMs carry a byte-to-symbol table for the name-entry screen (`$C1:1100`).
Its byte slots follow **gojuon order**, so identifying ONE slot pins the whole
block. Seed identifications came from cross-message name intersection: for each
English name appearing in >=N messages, the katakana sequence present in every
Japanese message at those same IDs. Names cross-validate each other (Doga/Boga
sharing ガ; four names sharing リ) before the table is ever consulted. A single
hiragana word ("Happiness" = しあわせ) then anchored the hiragana block, and
every other name-derived kana had to land on its predicted slot: 19/19 katakana,
7/7 dakuten. Blocks placed positionally without an independent hit must be
flagged as unvalidated - two such guesses here (a punctuation mark and the
handakuten block) were later proven wrong by photographs, and were catchable
only because they were flagged.

### 3b. Photographed tier: emulator VRAM dumps of rendered dialogue

With a dialogue box on screen, the emulator's VRAM export contains the rendered
text as a bitmap. Read the Japanese off the image, find that exact message in
the decoded script (search on already-mapped kana), and align: every unmapped
code lines up with a visible character. This is proof, not inference. Yield is
5-10 characters per capture; kanji-dense speakers (kings, priests, scholars,
signs) pay best, and all-kana lines (animals, shop prompts) pay nothing.

### 3c. Derived tier: the parallel corpus

The decisive lever. The translated portion IS a parallel corpus: Japanese and
the translators' English at the same message ID. For an unmapped kanji, the
surrounding okurigana pins the reading and the English names the concept -
together they usually force a single answer ([X]門 + "Watergate Key" = 水).

**Validate the method blind before using it**: run it over kanji already
photo-confirmed with the answers hidden. Here it scored 10/10. Then:

- Record evidence per entry, in the source, so any entry can be re-litigated.
- Refuse to map when the English does not force an answer. Every refusal here
  was vindicated: the "obviously 、" symbol was 「, the "resident font" was the
  sound engine, the 度/回 pair was swapped and only a new forcing context
  (回復) caught it.
- Compounds crack pairs at once (研究, 冒険の書, 千里眼); a wrong candidate
  usually fails loudly somewhere else in the corpus.
- Plateau behavior: rounds yield 15-30 characters until only corpus-blind codes
  remain (symbols appearing solely in untranslated messages). Those need
  photographs or a human reading; a dossier per code - all occurrences, full
  readable context, the English where any exists - resolved 10 of the last 13
  here by reading alone.

### The two-tier discipline

Photographed = proof. Derived = forced inference with cited evidence and a
measured blind-validation rate. Keep them separate in the data; if they ever
conflict, the photograph wins. Three inferences were overturned by photographs
in this project; all three were in the flagged/unvalidated category, which is
exactly the system working.

## 4. Authoring rules measured from the translators' own text

Voice and mechanical limits both come from the 6,544 messages they finished.

- **Mine their script for phrasing precedent before coining anything.** Their
  own "Unfortunately, the bed has disappeared" became the template for the
  save-erased lines. Where they have no term, flag the coinage for sign-off
  rather than inventing silently.
- **Names**: build the glossary from the ROMs (name intersection again). Theirs
  may be nonstandard (ルイーダ = "Luisa", アモール = "Amoru", シエーナ =
  "Shiena") - consistency with their choices beats correctness against any
  official source. Scan the untranslated block for katakana with no glossary
  entry and flag those separately; real-person names have no single correct
  romanization.
- **Layout caps, measured not guessed**: their pages ran to 104 visible chars
  (p99 = 72), segments to 81, name-token segments to 73. The engine scrolls
  rather than clips, BUT the scroll/replay buffer here is the same buffer with
  the known unbounded fill (+136 bytes measured at their own page sizes), so
  exceeding their maximum enters an unmeasured buffer regime. Hard cap at their
  max, work at their p99, and **add a page break rather than run long**.
- **Preserve the Japanese {AF} page positions**; treat JP {AD} line breaks as
  mechanical (Japanese has no word wrap) and write flowing English for the VWF
  wrapper, using {AD} only for deliberate breaks. Preserve every control code
  exactly; text around a runtime name token must read correctly for any name.
- **Pilot on one full scene, not scattered lines.** Independent system messages
  prove register; only a scene proves voice across a conversation.

## 5. Space

Measure, do not assume: encoded cost of existing English per Japanese source
symbol (6.478 bits here), times the untranslated Japanese volume, against the
dead space freed by English compressing smaller than Japanese (26 KB here,
2.8x need). The encoder from step 1 makes the eventual insertion mechanical;
nothing in this method requires touching the ROM until authoring is reviewed.

---

*Companion tooling: `dq6_extract_placeholders.py` (the glyph map with per-entry
evidence), `dq6_roundtrip.py` (the gate), `dq6_script_census.py` (the census).*

## 6. Style rules measured, not felt (added after the pilot review)

- **The mid-sentence "!" tic** ("You're! travellers, right?"): measured at 84
  occurrences across 6,541 messages, 1.1 percent - and it is CONTEXTUAL, not a
  frequency: it lands where the Japanese carries an explicit mid-thought
  hesitation (……). Rule: reproduce the tic exactly where the JP hesitates,
  never elsewhere. New text that is uniformly cleaner than the original is as
  much a tell as text that is sloppier.
- **Item and spell names without NoPrgress precedent**: their script is
  DW-era ("Firebal" with one L, "Fairy Water"), and they kept Japanese romaji
  (Madante) only where no NES-era term existed. Rule: NES-era Dragon Warrior
  convention first (earlier than this translation, so not a "later official
  localization"), romaji or coinage only when neither era has a term, and the
  reasoning recorded in the line note.
