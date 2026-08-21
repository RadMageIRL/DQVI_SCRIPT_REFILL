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

*Companion tooling, in `tools/`: `census.py` (the census, and `--roundtrip` is
the gate), `charset.py` (the trees and the byte table), `nametable.py` (the
second string system), `verify.py` (a build against its source). Each reads a
ROM you supply and prints; none of them writes anything.*

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
| `$559` | opening mark for untagged NPC speech | 519 message-initial; no JP counterpart, so it is their addition. **It has no glyph. See below** |
| `$576`/`$579` | `『 』`, for signs and written text | 38/38 align with JP `『` |
| `$577`/`$578` | inline quotation pair | 13 uses each, wrapping quoted words |

Two lessons generalize. First, **a convention at 92 percent is obligatory** and a
convention at 12 percent is optional: measure the rate before adopting one.
`$240` follows 91.9% of speaker tags, so new text that omits it is visibly
foreign; `$559` opens only 12.6% of NPC lines and varies by region of the script
(6% to 40% across ID buckets), so omitting it matches the majority everywhere.

That reading of `$559` was correct about the rate and wrong about the thing.
It turned out to have no glyph and to sit after a mark the engine already
draws, so the honest answer was not to match its rate but to delete it. The
measurement was fine; what was missing was ever looking at it on a screen.

Second, and more important:

**The writable alphabet is the Huffman tree, not the font.** Because the
insertion is gated on re-encoding with the *existing* trees, a symbol with no
code path in those trees cannot be written at all, whatever the font contains.
Enumerate it directly by walking the trees:

- English trees: **123 encodable symbols**. Japanese trees: 1,065.
- The music note `$634` is encodable in Japanese and **not** in English. It is a
  hard limit, not an oversight, and no amount of authoring skill recovers it.
- The tilde slot `$559` *is* encodable, but the translators repurposed it for
  the NPC speech mark above, so a literal tilde is equally unavailable. And
  encodable turned out not to mean drawable: see the next section.

Do this enumeration before authoring, not after. "The glyph does not appear in
their text" and "the glyph cannot be written" are different claims with
different consequences, and only the second one is a constraint.

### A symbol can be encodable, used, and still have no glyph

The enumeration above answers "can this be written". It does not answer "does
anything sensible appear when it is". Those come apart, and this project shipped
two releases before noticing.

DQ6's script carries symbol `$0559` 676 times, mostly opening a line of NPC
speech. It encodes, it round trips, it survives every structural check, and the
original translators used it deliberately and consistently. It also has **no
English glyph**: it is a full-width Japanese character that was never replaced,
so it drew a stray two-part mark before the first word of the sentence.

Nothing in the pipeline could see that. A decoder maps it to a placeholder and
moves on; a round trip reproduces it perfectly; a length audit counts it as one
glyph. The only instrument that catches it is a screen, and it took a player
asking "what is this mark" to raise it.

**Keep a list of the symbols you have never seen drawn.** The glyph map here
recorded `$0559` as an unresolved box for months. That box was the finding, and
it sat in the data being treated as a rendering detail rather than as an open
question. Anything the map cannot name should be counted, ranked by how often
the script uses it, and worked from the top. `$0559` was the fourth most common
message-initial symbol in the entire script.

### Establish what a glyph draws before deciding what to do about it

The fix took three attempts. The two wrong ones are the instructive part, and
they failed in opposite directions.

**First attempt: substitute.** From the data the marker looked like a single
wide glyph, because the message opened on `$0559` and the next symbol was
already the first letter of the first word, so everything drawn before that
letter had to come from `$0559`. The screenshot showed three marks. One symbol,
three marks, therefore one wide glyph. The reasoning is valid and the conclusion
was wrong: **the renderer draws things the message data does not contain.** Two
of the three marks were the engine's. Substituting the plain asterisk produced a
visible double star, and that build is what proved the symbol was redundant
rather than merely ugly.

**Second attempt: keep some.** Once it was clear the symbol should go, a
mechanical discriminator appeared: does the *Japanese* message at the same ID
open with an explicit marker pair rather than relying on the engine? For 20 of
the openings it does, all shop-clerk lines. That looked decisive, since the
source spells the mark out there, so those 20 were held back on the reasoning
that dropping them would leave those boxes unmarked. Also wrong. The engine
draws the mark in shop windows too, and a shop clerk in the build that had
already dropped them still showed it. The discriminator was real, well
measured, and answered a question nobody needed answered.

**What worked was the same instrument both times.** A villager, then a shop
clerk. Each took one save file and one conversation, and each settled in seconds
what a day of reasoning had got backwards.

Three rules, in the order they would have saved time.

**When output has more parts than input, suspect the renderer.** Message data,
engine-drawn decoration and font composition all reach the same window.
Counting symbols tells you about one of them.

**A measurement can be correct and irrelevant.** The Japanese-explicit-pair
split was real and reproducible. It was also a fact about the source data that
had no bearing on what the engine draws, and it was used to justify holding
back a change. Before acting on a discriminator, say which observable it
predicts, then check that observable.

**A comparison is only as good as its control.** The right test was always to
render one line that uses the symbol against one that does not, in each context
where it appears. It was proposed early and skipped twice in favour of arguments
from structure, and each skip cost a release.

### Minority conventions are a final mechanical pass, not a per-line decision

A convention used by 92 percent of the source is a rule you follow while
writing. A convention used by 12 percent is not: deciding it line by line
produces a distribution that reflects the author's mood, and the most likely
outcome is zero, because there is never a specific reason to reach for it. New
text that is uniformly cleaner than the original is a tell, and uniformly
*plainer* is the same tell.

Handle these by deferring them. Author without the mark, flag it, and apply it
at the end in one scripted pass whose target is measured rather than chosen.

This project planned exactly that pass for `$559`, the untagged-NPC speech
mark, with a measured per-region target rather than a global one, eligibility
decided structurally, and a re-measurement afterwards to prove it landed inside
the neighbouring rate. The design was sound and the shape is worth copying.

It was also aimed at the wrong symbol. `$559` has no glyph and duplicates a
mark the engine draws, so the correct action was to remove all 676 of its
occurrences, not to spread it across new ones. The pass that eventually ran was
the opposite of the one planned.

Keep the shape, and add a precondition to it: **before deferring a convention
to a mechanical pass, confirm the thing you are about to multiply renders
correctly.** A rate is a property of the source; a glyph is a property of the
screen, and only one of those is visible in a corpus.

The same shape applies to any minority habit: measure the rate, defer the
decision, apply mechanically, verify by re-measuring.

## 7b. Solve the format against itself, and stop asking what the output looks like

Section 7 is about a fallback that produced plausible output. This is the
answer to it, and it arrived last, after seven faults of that shape had each
been found by accident. Every one of them survived review because the rendered
text read correctly. **If plausible output is what fools you, stop grading
output.**

Most binary text formats carry redundancy: a length field, an offset, a count,
a checksum, a terminator, a pointer that must land where the previous record
ended. Each of those is an equation relating things you want to know. Enough of
them and the format tells you its own parameters, whatever the glyphs look like.

The worked example. DQ6's name table breaks a line with a code equal to
`0x90 + the number of characters already drawn on that line`. So every break
code in the ROM is one equation in the displayed widths of the codes on that
line. There are 164 of them. Most contain a single unknown, so the set falls
out by substitution, and the leftovers become a consistency check: 158
satisfied, none unsatisfied.

That measurement never looks at a glyph. It cannot be fooled by a sequence that
reads correctly with a character missing, which is exactly the fault it caught:
seven dictionary codes draw a trailing or leading space, and a decoder that
drops it still produces fluent English. `Mudo'` + `$F2` + `Castle` renders as
`Mudo'sCastle`, which passes for a packing quirk.

Three properties make this worth reaching for first rather than last.

**It is independent of the thing being checked.** A decode and a re-encode with
the same table agree with each other whatever the table says. An equation
derived from a length field does not care about the table at all, so the two
can disagree, and a check that cannot disagree is not a check.

**It scales without judgement.** 164 equations cost nothing to solve and no
attention to read. Reviewing 2,048 decoded entries by eye costs a day and
catches less, because the eye is looking for text that reads wrongly and this
class of fault reads correctly by construction.

**It says when it does not know.** Codes that never appear before a break code
are unconstrained, and the solver reports them as unsolved rather than assuming
them. That list is the exposed set, and it is short enough to settle another
way.

The general move: before trusting any table you reconstructed, find a field in
the format whose value is determined by the thing the table describes, and
check that the table predicts it. Length fields, offsets and counts are all
usable this way. If the format has none, the next best thing is what section 1
does with the pointer table, and the best thing of all is what this project
should have done from the start with the dictionary: **read the table the
renderer indexes, rather than reconstructing one.** The expander's own
instructions carry the address, the entry width and the range. Reconstruction
can drift; a read cannot.

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
found, because FOUR rounds of mechanism were proposed from screenshots and all
four were wrong, and two of them matched the corrupted cell counts exactly.

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
their script. It is not a bug the translators introduced or could have seen: it
has been latent since their release and only new text could reach it.

**The fix was to write those 194 page breaks in their form**, and it was
confirmed in play at the message that first showed the fault, along with
multi-page dialogue elsewhere in the build that the fix was not tuned to.

### The crash-fix patch was suspected and is exonerated

A plausible chain of reasoning implicated an unrelated patch: it had relocated
three word-wrap variables out of a block the game clears wholesale, so an
implicit initialization those variables had been getting for free was gone. If
one of them were the clear origin or a row bound, an off-by-one-row clear is
exactly this symptom.

That was wrong, and the way it was settled is worth copying. The obvious test,
running the crash-fix patch WITHOUT the new text, cannot decide anything: with
no new text there are no page breaks that open on a letter, so the path is
never taken and a clean result proves nothing. The decisive build is the other
diagonal: **the new text with the fault still in it, and the crash-fix patch
absent.** That build corrupted identically, which puts the fault in stock
behavior and clears the patch completely. No notice was needed anywhere.

The general point: when isolating a fault between two changes, check whether
each cell of the matrix can actually reach the fault. A cell that cannot
exercise the code path produces a clean result for the wrong reason, and
reading that as evidence is how a wrong conclusion gets a confident number
attached to it.

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

Independently of the fault, 401 hard line breaks across 258 messages were
merged out to bring this draft into line with theirs: 0.56 breaks per message
and a mean segment of 37.0 visible characters, against their 0.63 and 38.0, and
against this draft's own 1.52 and 24.1 before. They write long lines and let the
variable-width font wrap; this draft had been breaking explicitly and often.

**That is a VOICE change, not a fix. It contributed nothing to the correction
above** and must not be described as having done so: it was made while chasing
the fault, on a hypothesis that turned out to be wrong, and it survives on the
distribution match alone. Its cost is recorded honestly: 20 pages now sit above
the 72-character working target, up from 11, none near the 104 hard cap, which
is the direct consequence of writing lines as long as theirs.

---

## 10. A wrong pairing method produces plausible readings

Section 7 is about a fallback that produced plausible output, and 7b is the
answer to it. This is the same failure in a different place, found during the
completeness pass, and it is worth its own section because the wrong answer was
not merely plausible. It was interesting.

The name table exists in two ROMs and entries have to be paired across them.
Three shift theories preceded the ID rule, all measured against entry POSITION.
The reason a shift keeps looking right is that positions diverge slowly: the two
tables pack different numbers of bytes, so a shift fitted on a handful of
anchors holds for a stretch and then stops, and it stops somewhere nobody
checked.

**What position-based pairing returned.** Resolved by position, the block at
entries 1931-2005 reads as skill descriptions, split across lines the way this
table splits everything:

```
いなずまを / よびよせ        summons lightning
つるぎの / さみだれ          sword flurry
ドラゴンの / うろこを / きりさく   cuts through dragon scales
```

Seventy-five consecutive entries, all coherent, all in the register the block
should be in, all split at plausible line breaks, and every one of them
addressable by a live string ID. The conclusion that followed was that seventy-five
player-facing skill descriptions were still showing `M`-codes in a shipped
release.

**Resolved by string ID, the same block is the naming-screen obscenity list.**
Not one word of it is ever drawn.

The reading was not a near miss or a garbled approximation that careful
attention would have caught. It was fluent, structured and thematically
consistent, because a wrong offset into a table of natural-language strings
returns natural-language strings. **Plausibility is not weak evidence here; it
is the expected output of the failure mode.** A pairing method that returns
nonsense when wrong is safer than one that returns prose.

So the check cannot be "does the result read correctly". It has to be a property
the wrong method cannot satisfy. Here it is that the resolver at `$C0:3190` is
byte-identical in both ROMs, so string ID X **is** the same string in both by
construction, and no fitting is involved at all. The ID rule then holds 348 of
348 in the stock ROM and 170 of 170 in the release.

**If a constant shift seems to work, that is the failure mode, not a discovery**
- and if the output of a shift reads beautifully, that is not reassurance.

## 11. Internal strings are not required to be in a second language

Seventy of the entries still showing an identifier turned out to be map-editor
and debug-menu labels: tile attributes, castle map slots, a debug menu with a
cheat-Zoom and a sound test, a window debug block.

They were missed for months, and the reason is a single unexamined assumption.
The editor labels found earlier were Latin - `EDIT`, `RESIZE`, `OBJ0`, `LV3`,
`X:`, `Y:` - and finding them depended on working out that Japanese bytes
`$8C`-`$A5` are the full-width Latin alphabet. That find was real and it worked,
and it quietly installed the idea that **internal strings look like `OBJ0`**. So
the search was for Latin identifiers, and everything not matching that shape was
treated as content awaiting translation.

Enix's developers wrote their debug menu in Japanese, which is the unremarkable
thing for a Japanese studio to do. `いんちきルーラ` is "cheat Zoom".
`サウンドテスト` is a sound test. `ほこうテスト` is a walk test. These sat in the
census as untranslated content, indistinguishable by shape from a real item
name, for as long as the question being asked was "is this Latin".

**The lesson generalizes past this ROM.** A debug string is identified by what it
does, not by what alphabet it is in. The discriminator that works is meaning:
`レベル0` next to `ウインドウデバック` is a debug block whatever script it is
written in. The discriminator that failed is orthography, and it failed silently,
because an untranslated debug label and an untranslated item name are the same
shape in every measurement except reading them.

---

## 12. They had two placeholder conventions, and the radix proves it

The `M####` rule is established: an untranslated name-table entry displays its
own string ID in hex. The message script has its own form, bare decimal digits,
plus a rarer `TEXT####`. Nobody had asked whether these came from the same tool,
and the answer is measurable.

**They are in different number bases.**

| system | form | radix | count |
|---|---|---|---|
| message script | bare digits, `TEXT####` | **decimal** | 421 = 416 + 5 |
| name table | `M####`, `*###` | **hex** | 348 |

421 of 421 script placeholders match their own message ID in **decimal**, and
none matches in hex. 348 of 348 name-table placeholders match their own string
ID in **hex**, and none matches in decimal. Same idea - print the identifier
rather than the text - implemented twice with different settings.

**The two systems never borrow each other's form.** Zero messages match
`M####`. Zero name-table entries match `TEXT####`. A clean separation by system
is what two tools, or two passes, look like.

**But the counter-observation matters and is recorded deliberately.** Within the
script the two forms interleave rather than sitting in separate stretches:

```
6289  bare digits
6290  TEXT6290
6291  TEXT6291
6292  bare digits
```

So `TEXT####` is not a later pass over the script, and not an earlier one. Five
messages out of 421 took the other form while their immediate neighbours did
not, which means something about those five, not about when the work was done.
**A hypothesis that explains the split between the systems does not
automatically explain the split inside one of them.**

### The full prefix census, so nobody has to guess again

```
name table   M 313   * 35                          348, all hex == own string ID
             S 21  K 11  ID 10  E 1  D 1  DS 1  C 1   46, Latin in the Japanese
script       bare digits 416   TEXT 5              421, all decimal == own ID
```

No other prefix exists in either system. The 46 are not emitted identifiers at
all - the Japanese ROM holds the same Latin strings, which is why they do not
follow the ID rule.

### A second marker with an unidentified trigger

`*` is not a variant spelling of `M`. It is confined to entries 1338-1599, the
skill-description region, and interleaves with `M` inside that band.

The obvious hypothesis was that `*` marks a mid-sentence continuation fragment,
since the region is full of them. **Tested and refuted.** Taking the final
character of each entry's Japanese, in that same band:

```
ends in a grammatical particle:   *  14 of 35  (40%)
                                  M   8 of 14  (57%)
```

`M` entries end in a particle MORE often than `*` ones, so `*` is not marking
grammatical continuation. It is a real second marker and its trigger is still
unknown.

That is worth recording as an open question rather than a footnote. Every
convention of theirs that has been worked out has explained something later -
the ID rule gave the Japanese for 348 entries, and the full-width Latin map
turned eleven apparent kanji into editor labels and stopped three map slots
being given invented names.

---

## 13. Ask what selects the entry, not what it looks like

`$06FD` held a single kana, `し`, sitting last in the Goof-off block between
`Squish Squish` and the skill-description fragments. Two readings were argued
from position and both were wrong.

**First it was read as the tail of a split line**, since a bare kana looks like a
continuation. That died on a measurement: **zero of 2,048 entries end on a break
code**, so break codes appear only inside an entry and nothing continues across
an entry boundary.

**Then it was left as unresolved content** on the grounds that it was a genuine
addressable slot, which it is. That was also wrong, and the reason is that
being addressable and being used are different things.

**The question that settled it was what selects it.** Abilities live in a table
of 25-byte records at `0x08C674`, each beginning with its name's string ID. The
Goof-off pool is records 351-407, IDs `$06C4`-`$06FC` - the command label `あそび`
plus **56 actions** - contiguous and bounded by null records at either end.

```
no record in that table carries $06FD      checked across all 409
$06FC  has one, index 407
$06EB  has one, index 390
```

So `し` is a name-table slot that nothing selects. It is not a translation gap;
it belongs with the internal entries. And the same measurement cuts the other
way for `$06EB`, which does have a record, mid-run, so it is a real selectable
action whose name we still cannot read. The "unused slot" explanation died for
that one at the same moment it was confirmed for this one.

**One trap worth naming.** Striding blindly past the end of the table produced a
"record" for `$06FD`, which is what first suggested it was an ability. The table
stops at record 408 and what follows is a different structure - an index of
record offsets, `0, 25, 50, 75...`, in multiples of the stride. The bytes that
looked like an ID were a bare word between the two tables. **A record has a
shape; check it against a known-good one before believing an entry exists.** A
real record here carries stat fields, and that address carried an arithmetic
sequence.

**The general rule:** for any entry whose category is in doubt, the useful
question is not what its text looks like or what its neighbours are. It is
which table references it. Adjacency produced two wrong answers here and a
reference check produced the right one in a single lookup.

---

## 14. When their rendering blocks ours, and the rule that keeps it narrow

This patch changed one piece of NoPrgress's own text. It is the only one, and
the circumstances are worth stating exactly, because the reasoning generalizes
badly if it is loosened even slightly.

`$070A そうぞうを` was untranslated. `$070B ぜっする` was theirs, rendered
`Really`. The two are the halves of 想像を絶する, "beyond imagination", and the
first half cannot be written faithfully against the second: any correct English
for `そうぞうを` reads as nonsense next to `Really`. Their rendering was not
merely loose, it was **load-bearing on an entry that could not be completed
around it**.

**The rule, stated so it cannot widen:**

> Their text is changed only where their rendering blocks completing an
> untranslated entry. Not for clumsiness, not for style, not for accuracy alone.

Every clause is doing work. `Really` for `ぜっする` is inaccurate, and that on
its own would not have justified touching it - the table is full of loose
renderings this patch leaves alone, `Spy` for `かみわざ` among them. What
qualified it is that an unwritten entry sat immediately beside it and could not
be written while it stood.

**The check that made the cost measurable.** Before changing anything, count the
other uses. `ぜっする` occurs exactly once in the table and `Really` was used
exactly once, so the change could not break a second line. **Had it appeared
twice, this would not have been done**, because fixing one description while
breaking another is not an improvement and the trade stops being narrow.

**The words sit across the pair rather than glossing each entry.** `$070A`
became `Beyond` and `$070B` became `Imagining`, so `そうぞうを` no longer
matches its entry word for word. That is their own practice here, not a
liberty: `$0717 ちからをあわせ` means "combining power" and they render it
`Fury of` precisely so that `Fury of` / `The gods` reads in ascending order.
Fragments are assembled, so what has to read correctly is the assembled line.

**What was NOT claimed afterwards.** The README used to say "not one word of
their writing is altered". That is no longer true and the sentence was replaced
rather than qualified into meaninglessness: their **dialogue** is untouched,
verified symbol by symbol on every build, and exactly one name-table entry of
theirs is changed, named, with the reason given. A promise that has acquired an
exception is worth less than an accurate description of what was done.

---

## 15. Enumerate the emit sites, not the entry

`$011C がた` was the last entry settled by measurement rather than argument, and
it is the cleanest result of the whole effort. It is worth recording as a
pattern because it is cheap and it is exhaustive.

The entry is a runtime suffix, so the question was what it attaches to. Two
readings demanded opposite English and picking wrong produced either `Yous` or
`Slime all`, so nothing could be written until one was eliminated. Neighbours
could not settle it: `$0118 たち` is `s` two entries away, and `$011E あなた` is
`You` two entries the other way.

**The measurement was to enumerate every site that can emit a name-table string
through the message system.** One pattern, `LDA #imm` followed by `JMP $920C`,
across the whole ROM. It returns **five sites**, four of them name-table
strings:

```
$0118  たち      s
$011C  がた      <- the entry in question
$011D  みなさん  Everyone
$011E  あなた    You
```

That is the complete family, and three of the handlers are **byte-identical
apart from the string ID**:

```
JSL $C42B1C      the shared test
... DEC A
BEQ -> RTL       emit nothing when the result is 1
LDA #$0118 / #$011C / #$011D
JMP $920C        emit
```

`がた` fires on the plural branch exactly as `たち` does, so it takes the same
English plural, `s`. And the `あなた` reading dies on the same evidence rather
than on judgement: `あなた` is emitted on the OPPOSITE branch of its handler,
the singular one, so `がた` and `あなた` are conditioned oppositely and **can
never both fire**. `あなたがた` is not constructible from these handlers.

**Why this beats what came before.** Every earlier attempt on this entry reasoned
from what sits next to it. The emit-site enumeration does not care about
position at all: it asks which instructions can put this string on screen, and
there turned out to be one, with two siblings that name its category. **A
complete enumeration of a small set beats any amount of reasoning about a large
one.**

### The same check, applied to two entries, returning nothing

`$014D ばか` and `$014E かみ` were put through it and came back empty, which is
worth recording as a result rather than a silence.

Neither appears in the ability table. Neither is a JSL argument to any string
routine. Both `LDA #imm` sites for `$014D` feed `$C0:0D0C`, which writes
`$004202`, the hardware multiply register - so that is the number 333, not a
string ID. `$014E`'s two sites write `$5E8E`, a general parameter slot used 136
times across the ROM with all manner of immediates.

**That is a stronger position than "the neighbours are ambiguous", and it is
still not proof.** With 612 callers into the main string routine, nearly every
reference in this game is computed rather than literal, so an absent literal
load carries little weight on its own.

There is a data blob at `0x023C71` containing both, inside an ascending run that
excludes the `X:` and `Y:` editor labels. It is recorded as **suggestive and
nothing more**. Three apparent structures dissolved under examination during
this work - a "curated list" that was a segmented ascending run, a group of
eight that could not be told from event bytecode, and a "record" for `$06FD`
that was an index table past the end of the real one. The caution is worth more
than the pattern.

---

## 16. When a guess is cheap to correct, the balance moves

Two entries, `$014D ばか` and `$014E かみ`, were written on reading alone. Both
went through the reference check that settled `$06FD` and `$011C` and both came
back empty, so there is **no positional evidence for either** - no ability
record, no JSL argument to a string routine, and their only literal loads feed a
hardware multiply register and a general parameter slot. They are the weakest
calls in this patch and the docs say so in those words.

For most of this work the rule was that a gap beats a confident wrong answer,
and that was right while a wrong answer would have been **untraceable**. The
thing that changed is not the confidence. It is the cost of being wrong.

**What makes a guess cheap to correct:**

- **The chain is recoverable.** Every version is tagged with its patches
  attached, so any build can be reproduced and any change can be undone.
- **The data is keyed by the game's own identifier**, not by position or by
  order. A correction is one row in `nametable-en.txt` and a rebuild, and it
  cannot disturb anything else, because the builder repacks the whole table
  from the file every time.
- **The basis is written down.** Each inferred entry names what it rests on and
  what the competing reading is, so someone who disagrees can check the specific
  thing rather than relitigate the judgement. `かみ` records the case for
  `Hair` - the two 髪 uses in the table and the `Accessories` adjacency - beside
  the case for `God`.
- **The failure is visible.** These render on screen. Anyone playing the scene
  sees the answer immediately, which is the one form of verification this
  project has repeatedly found to beat every static check.

Under those four conditions the arithmetic inverts. **A wrong guess costs a
commit. An identifier on screen costs a player**, every time that scene is
reached, permanently.

**The conditions are the point, not the conclusion.** Remove any one of them and
the old rule comes back. If the data were keyed by position, a correction would
risk moving its neighbours. If the basis were not recorded, a report could not
be checked and would turn into an argument about taste. If the entry never
displayed, nobody would ever find the error and the guess would harden into
fact. **Write the guess when it is cheap to correct and its basis is on record.
Leave the gap when it is not.**
