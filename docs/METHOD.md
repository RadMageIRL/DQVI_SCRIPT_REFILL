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
- **One context that admits two readings is not a forcing context.** This is the
  single commonest way a wrong glyph survives. If the evidence is `目[X]` glossed
  "objective", both 目的 and 目標 satisfy it, and mapping either one is a coin
  flip recorded as a fact. Refuse, and wait for a second context. Two glyphs in
  this project were mapped this way and both were wrong: one was caught only
  because debug text later produced non-words (座的, 的準), the other because a
  line read as nonsense during authoring.
- **Audit for that standard rather than waiting to be lucky.** The check is
  mechanical: for every derived entry, count the occurrences in *translated*
  messages, since only those carry English that can force a reading. Entries at
  zero or one are the exposed set. Most will be safe because a fixed compound
  locks them (甲板, 太陽, 千里眼, 確率), so the audit does not re-derive anything,
  it just produces a short list to read by eye. Here 296 derived entries yielded
  18 exposed, of which four needed action and one was an outright error that had
  been sitting quietly for weeks.
- **Corrections propagate; re-run the unmapped list after every one.** Fixing a
  glyph changes the context its neighbors sit in. Correcting 癒 to 直 immediately
  forced 接, which had been unmappable for as long as the glyph before it was
  wrong. A wrong entry does not just carry its own error, it suppresses the
  evidence for everything adjacent to it.
- Plateau behavior: rounds yield 15-30 characters until only corpus-blind codes
  remain (symbols appearing solely in untranslated messages). Those need
  photographs or a human reading; a dossier per code - all occurrences, full
  readable context, the English where any exists - resolved 10 of the last 13
  here by reading alone.

**When a term has no direct precedent, look at what the thing IS, not what it is
called.** The corpus method above searches for a word; this is the same method
turned sideways, and it is what to reach for when the word search comes back
empty.

A worked example. One message described four legendary weapons as bearing a
`もんしょう` each. That word occurs exactly once in 6,960 messages, so there was
no precedent and the obvious move was to coin something ("emblem") and flag it.
Instead, catalogue the *objects*: find all four weapons by name, then read every
message that describes them. The game turns out to describe those same engraved
sigils elsewhere using a different word, `しるし`, which the translators had
already rendered as **"mark"** - same verb (`きざまれている`), same four objects,
different noun. The coinage was withdrawn in favor of their own vocabulary.

The same pass produced two further corrections for free: it established all four
weapon names, which showed that an earlier authored line had used a possessive
form where the translators used "the X of Y"; and it resolved a character name
that had been parked as unglossed katakana for weeks. That yield is the argument
for the method. Searching for the word answers one question and stops; reading
the descriptions of a thing's siblings answers the question you asked and several
you had not got to yet.

Generalized: when precedent is missing for a term, enumerate the set the term
belongs to, pull every message mentioning any member of that set, and read them.
Fan translations describe their own world constantly, and a thing is usually
named indirectly somewhere even when it is never named directly.

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
- **A page break is a pacing tool, not only a length constraint.** The rule above
  is about fidelity, and the length rule before it is about safety, but `{AF}` is
  also the only instrument the format gives you for timing. A plot-bearing or
  emotionally weighted line can take its own page so the reader stops on it, and
  a comic swerve can take one so the setup and the punchline do not arrive in the
  same glance. Two worked examples from this project: a villager admitting nobody
  can remember when two orphans arrived at the church, isolated on a short page
  because the strangeness is the point and it is easy to skim past inside a
  paragraph; and a stammered joke split exactly where the Japanese pivots, so the
  chicken-out lands as a second beat. This is the same sanctioned addition as
  splitting an over-long page, with a different reason, and it carries the same
  condition: **add** a break, never move or delete one the Japanese put there.
  Record the reason in the line note, so a later pass can tell a pacing break
  from a length break and does not "tidy" it away.
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

## 7. Read this section first: a plausible fallback will hide a subsystem

This is the most important thing this project learned, and it is a warning
about your own tooling, not a note about ours. Every reader of this document
has written the line below, or one like it, and it is worth going to look.

The single most damaging line of code in this project was in the analysis
renderer, not in anything that touches a ROM:

```python
CH.get(symbol, ' ')      # unknown symbols fall back to a space
```

One character of fallback. Every symbol the character map could not name
rendered as a space, and a space is *legal output*. So the decoded script
looked correct. It read as fluent English. It was reviewed repeatedly, quoted
in three documents, and used as the evidence base for authoring rules. It was
missing an entire punctuation system: a speaker-tag quote used 3,290 times, a
speech mark used 658 times, two bracket pairs, and a hyphen that had been
mis-read as a second comma so that their "puff-puff", "bare-handed",
"Dream-Seeing Drops" and "Goof-off" all silently displayed as commas.

Three things generalize, and the third is the uncomfortable one.

**A fallback that renders as plausible output is worse than a crash.** A crash
is a bug report. Plausible output is a wrong belief with evidence attached, and
it recruits every downstream artifact into agreeing with it. Render unknown
symbols as a loud placeholder that could never be mistaken for content, and
count them. If the count is not zero, no conclusion drawn from that render is
safe yet.

**The corrupted conclusion looked like a finding.** "Their speaker convention is
name + space" was measured, reproducible, consistent across thousands of
messages, and false: the space was the fallback. Reproducibility does not
protect you here, because the defect is upstream of the measurement and is
perfectly consistent. Ask of any structural claim: could my renderer produce
this appearance from something that is not this?

**It surfaced through an unrelated question.** Nobody found it by auditing the
renderer. It fell out of a question about whether a music note glyph existed,
which required checking what a symbol code meant in one ROM versus the other,
which is the one operation that goes around the fallback. Deliberate review of
the code would probably never have caught it, because the code is correct in
isolation and only wrong in what it implies. **Follow the odd question.** The
cheapest audits of a decoding pipeline are the ones that approach a value by a
second, independent path, and they are usually prompted by something that looks
like a tangent.

The corollary for planning: schedule at least one adversarial re-derivation of
anything a large body of work rests on, from a different direction than the one
that produced it. Here that would have been "name every symbol the translators
actually used", which takes an afternoon and would have caught all of it.

## 7a. The charset is smaller than the font, and it is measurable

Once the fallback was fixed, the parallel corpus named the missing symbols in
one pass. In this ROM the translators' English uses:

| symbol | role | evidence |
|---|---|---|
| `$240` | opening quote after a speaker tag | 3,290 uses, 99.8% within 14 symbols of a `{D4}` tag; 1,489 align with JP `「` |
| `$559` | opening mark for untagged NPC speech | 519 message-initial; no JP counterpart, so it is their addition |
| `$576`/`$579` | `『 』`, for signs and written text | 38/38 align with JP `『` |
| `$577`/`$578` | inline quotation pair | 13 uses each, wrapping quoted words |

Two lessons generalize. First, **a convention at 92 percent is obligatory** and a
convention at 12 percent is optional: measure the rate before adopting one.
`$240` follows 91.9% of speaker tags, so new text that omits it is visibly
foreign; `$559` opens only 12.6% of NPC lines and varies by region of the script
(6% to 40% across ID buckets), so omitting it matches the majority everywhere.

Second, and more important:

**The writable alphabet is the Huffman tree, not the font.** Because the
insertion is gated on re-encoding with the *existing* trees, a symbol with no
code path in those trees cannot be written at all, whatever the font contains.
Enumerate it directly by walking the trees:

- English trees: **123 encodable symbols**. Japanese trees: 1,065.
- The music note `$634` is encodable in Japanese and **not** in English. It is a
  hard limit, not an oversight, and no amount of authoring skill recovers it.
- The tilde slot `$559` *is* encodable, but the translators repurposed it for
  the NPC speech mark above, so a literal tilde is equally unavailable.

Do this enumeration before authoring, not after. "The glyph does not appear in
their text" and "the glyph cannot be written" are different claims with
different consequences, and only the second one is a constraint.

### Minority conventions are a final mechanical pass, not a per-line decision

A convention used by 92 percent of the source is a rule you follow while
writing. A convention used by 12 percent is not: deciding it line by line
produces a distribution that reflects the author's mood, and the most likely
outcome is zero, because there is never a specific reason to reach for it. New
text that is uniformly cleaner than the original is a tell, and uniformly
*plainer* is the same tell.

Handle these by deferring them. Author without the mark, flag it, and apply it
at the end in one scripted pass whose target is measured rather than chosen.

The criterion this project will use for `$559`, the untagged-NPC speech mark:

1. **Trigger:** all 416 lines authored and reviewed. Not before, because the
   run distribution is not known until then and the pass is worthless applied
   to a partial corpus.
2. **Target:** per region, not globally. For each authored run, measure the mark
   rate among translated messages within plus or minus 40 IDs. It varies from 6
   percent to 40 percent across the script, and the 3440-3520 neighborhood runs
   at 2 of 51, so a single global figure would over-mark some regions and
   under-mark others.
3. **Eligibility:** only lines that are untagged NPC speech. Lines opening with
   a `{D4}` speaker tag take the tag quote instead, and system or narration
   lines take neither. This classification is structural and scriptable.
4. **Verification:** re-measure after the pass and require the refilled lines to
   sit inside the neighbor rate for their own region. A pass that cannot be
   verified by re-measurement has not been done.

The same shape applies to any minority habit: measure the rate, defer the
decision, apply mechanically, verify by re-measuring.

## 8. Wordplay: rebuild the joke, do not explain it

Where the source gag is phonetic, a faithful gloss produces a line that is
accurate and dead. The rule is to rebuild the mechanism in the target language
and accept a different surface.

The worked example: a nervous suitor tries to say 結婚 (*kekkon*, marriage),
loses his nerve mid-word, and swerves into 結構さむい (*kekkou samui*, "quite
cold"). Three things make the joke work, and all three are reproducible without
the words: a shared onset, a collapse partway through, and the swerve landing
on a banality about the weather. Rendered as **"m- marry... marry... m-mighty
cold today, isn't it"** it keeps all three, including the position of the pivot
relative to the page break.

What to preserve, in priority order: the mechanism, the beat on which the joke
turns, the register of the speaker, and only then the literal content. A
footnote-style rendering ("he tries to say 'marriage' but says 'cold' instead")
fails on all four. If no rebuild is available, say so and flag the line rather
than shipping a gloss.

## 9. A render fault found by counting, not by looking

The last defect in this project was a text-window corruption: the first row of
every page after the first drew on top of the previous page's first row, so a
long message accumulated layers as it ran. It is worth recording how it was
found, because three mechanisms were proposed from screenshots and all three
were wrong, including one that was measured and still wrong.

**What settled it was a corpus-wide count of a structural invariant.**

Their 6,539 finished messages contain 4,638 page breaks. Tabulating what
follows each one:

| after a page break | count | share |
|---|---|---|
| a line break | 3,646 | 78.6% |
| end of message | 869 | 18.7% |
| another control code | 122 | 2.6% |
| **directly a letter** | **1** | **0.02%** |

The single exception sits inside a trailing-filler region past the last real
message, so across all real content the invariant is absolute: **a page break
is never followed directly by text.** The authored draft broke it 128 times.

That is the whole diagnosis. Their engine was never asked to open a page on a
letter, so that path was never exercised and the fault was never reachable in
their script. It is not a bug the translators introduced or could have seen.

Three lessons generalize.

**Look for invariants in the source, not mechanisms in the symptom.** A
mechanism guessed from a still image is a story that fits one frame. An
invariant holding 4,638 times out of 4,638 is a rule, and a draft that breaks
it 128 times is the defect whether or not you can explain the hardware.

**Beware the measured-but-wrong hypothesis.** One rejected explanation had real
arithmetic behind it: the corrupted cell counts matched the overflow of the
authored line past a plausible window width, exactly, twice. It was still
wrong, and it was killed by another measurement showing the translators' own
lines were longer than the ones supposedly overflowing. Numbers that fit are
not the same as numbers that discriminate.

**Test the thing you claimed to test.** A large edit was made to line breaks
INSIDE pages and reported as a test of the page-break boundary. It was not the
same edit. It touched none of the implicated sites and in fact raised their
count from 98 to 128. If a change is offered as a test, state the number it is
supposed to move and check that number afterwards.

### Layout style, kept as a separate matter

Independently of the fault, this draft's hard line breaks were brought into
line with theirs: 0.63 breaks per message and a mean segment of 38 visible
characters, against 1.52 and 24.1 before. That is a VOICE change, not a fix,
and it contributed nothing to the correction above. Its cost is recorded
honestly: 20 pages now sit above the 72-character working target, up from 11,
none near the 104 hard cap, which is the direct consequence of writing lines as
long as theirs.
