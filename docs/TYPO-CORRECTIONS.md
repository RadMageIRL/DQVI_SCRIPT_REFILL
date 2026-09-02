# Their spelling: every correction

This is the whole list, unchanged since v4.0 which introduced it. It is
generated from the two ROMs rather than kept by hand, and `tools/verify.py`
re-derives the same claims on every build.

The trailing asterisk dropped from five item names in v5.0 is a different
kind of change and has its own account in
[`ITEM-NAME-ASTERISK.md`](ITEM-NAME-ASTERISK.md).

**The rule, stated so it cannot widen.** Their text is corrected only where
one of these holds:

> **A.** the ROM itself attests the correct spelling elsewhere in their own
> writing, or
> **B.** the shipped form is not an English word and has exactly one English
> spelling.

Nothing else. No rewording, no register, no grammar, no punctuation, no
phrasing. Thirteen further candidates the same audit turned up are excluded
and listed at the end; they stay excluded.

`thiefs` -> `thieves` and `alot` -> `a lot` are in scope, which is why the
rule is written as above and not as "letters only".

## Count

| | misspellings | sites | player-facing | internal |
|---|---:|---:|---:|---:|
| message script | 64 | 76 | 74 | 2 |
| name table | 3 | 3 | 3 | 0 |
| **total** | **67** | **79** | **77** | **2** |

One misspelling, `aquired`, occurs once in a player-facing message and once
in an internal one, so the two site columns split it and the misspelling
column does not double it.

**The headline figure is 67 misspellings across 77 player-facing sites** -
74 in the message script and 3 in the name table. The remaining 2 sites are
event-flag strings the game never draws (`Became a soldier`, `Opened path to
Hell Cloud`). They are corrected for consistency and counted apart, because a
count that includes strings nobody can reach is not checkable by playing.

## Length

Measured before anything was applied. `cells` is drawn character cells, the
unit their own layout is bounded in. Their own maxima, measured across the
whole shipped script: **80 cells** in a segment (text between line or page
breaks) and **104 cells** in a page.

- 38 sites lengthen, 24 are neutral, 14 shorten
- net change across the whole script: **+20 cells**
- worst segment after correction: **74** of their 80
- worst page after correction: **74** of their 104
- **flagged sites: 0.** No line break is added, no page break moves, no page
  break lands on a letter, and every name-table correction is exactly
  length-neutral so no break code moves either.

## The corrections

`attested` is how many times their own text spells the corrected form
somewhere else. Tier B corrections have no attestation by definition: the
shipped form is not a word, and the correct spelling never appears in their
script at all. `/` is a line break, `//` a page break, `{XX}` a control code.

Two notes on the quoted text. `!` is symbol `$0246`; what that symbol draws
on screen is under separate investigation and this patch does not touch a
single one of them. `{SPK}` is `$0240`, the mark their speaker tags open on.

| ID | tier | shipped | corrected | delta | segment | page | attested |
|---|:---:|---|---|---:|---|---|---:|
| 31 | A | `Stength` | `Strength` | +1 | 27 -> 28 | 27 -> 28 | 21 |
| 64 | A | `wimpering` | `whimpering` | +1 | 11 -> 12 | 11 -> 12 | 1 |
| 155 | A | `aquired` | `acquired` | +1 | 28 -> 29 | 28 -> 29 | 18 |
| 191 | A | `forunate` | `fortunate` | +1 | 62 -> 63 | 62 -> 63 | 2 |
| 239 | B | `penninsula` | `peninsula` | -1 | 60 -> 59 | 60 -> 59 | - |
| 248 | B | `penninsula` | `peninsula` | -1 | 62 -> 61 | 62 -> 61 | - |
| 296 | A | `Mahamen` | `Mahamed` | +0 | 43 -> 43 | 43 -> 43 | 17 |
| 296 | B | `refering` | `referring` | +1 | 43 -> 44 | 43 -> 44 | - |
| 339 | A | `probaly` | `probably` | +1 | 33 -> 34 | 33 -> 34 | 24 |
| 361 | B | `porportional` | `proportional` | +0 | 74 -> 74 | 74 -> 74 | - |
| 374 | A | `decendant` | `descendant` | +1 | 65 -> 66 | 65 -> 66 | 1 |
| 380 | B | `convient` | `convenient` | +2 | 52 -> 54 | 52 -> 54 | - |
| 393 | B | `in in` | `in` | -3 | 54 -> 51 | 54 -> 51 | - |
| 409 | A | `Theather` | `Theatre` | -1 | 59 -> 58 | 59 -> 58 | 2 |
| 554 | A | `suprise` | `surprise` | +1 | 50 -> 51 | 50 -> 51 | 6 |
| 658 | A | `I'l` | `I'll` | +1 | 24 -> 25 | 24 -> 25 | 175 |
| 829 | A | `wimpering` | `whimpering` | +1 | 11 -> 12 | 20 -> 21 | 1 |
| 874 | A | `Unfiorms` | `Uniforms` | +0 | 31 -> 31 | 31 -> 31 | 9 |
| 966 | A | `Tommorow` | `Tomorrow` | +0 | 43 -> 43 | 43 -> 43 | 8 |
| 1003 | B | `siezed` | `seized` | +0 | 16 -> 16 | 61 -> 61 | - |
| 1044 | B | `occured` | `occurred` | +1 | 62 -> 63 | 62 -> 63 | - |
| 1093 | B | `alot` | `a lot` | +1 | 37 -> 38 | 37 -> 38 | - |
| 1202 | A | `did't` | `didn't` | +1 | 46 -> 47 | 46 -> 47 | 87 |
| 1228 | A | `embarrasing` | `embarrassing` | +1 | 51 -> 52 | 51 -> 52 | 1 |
| 1258 | B | `persistant` | `persistent` | +0 | 47 -> 47 | 47 -> 47 | - |
| 1389 | A | `basptism` | `baptism` | -1 | 48 -> 47 | 48 -> 47 | 10 |
| 1440 | A | `jounrey` | `journey` | +0 | 49 -> 49 | 49 -> 49 | 45 |
| 1493 | B | `devestation` | `devastation` | +0 | 23 -> 23 | 66 -> 66 | - |
| 1549 | A | `somwhere` | `somewhere` | +1 | 35 -> 36 | 40 -> 41 | 14 |
| 1606 | B | `inconvient` | `inconvenient` | +2 | 62 -> 64 | 62 -> 64 | - |
| 1701 | A | `yous` | `you` | -1 | 54 -> 53 | 54 -> 53 | 2740 |
| 1712 | A | `yous` | `you` | -1 | 54 -> 53 | 54 -> 53 | 2740 |
| 1779 | A | `stength` | `strength` | +1 | 61 -> 62 | 61 -> 62 | 21 |
| 1821 | A | `wher` | `where` | +1 | 32 -> 33 | 32 -> 33 | 128 |
| 1888 | B | `the the` | `the` | -4 | 52 -> 48 | 52 -> 48 | - |
| 1973 | B | `refering` | `referring` | +1 | 45 -> 46 | 45 -> 46 | - |
| 2278 | A | `Congradulations` | `Congratulations` | +0 | 64 -> 64 | 64 -> 64 | 10 |
| 2543 | B | `Foribidden` | `Forbidden` | -1 | 42 -> 41 | 42 -> 41 | - |
| 2663 | A | `enegergetic` | `energetic` | -2 | 50 -> 48 | 50 -> 48 | 6 |
| 2679 | A | `Riedock` | `Reidock` | +0 | 66 -> 66 | 66 -> 66 | 116 |
| 2820 | A | `choise` | `choice` | +0 | 56 -> 56 | 56 -> 56 | 9 |
| 2892 | A | `stroy` | `story` | +0 | 47 -> 47 | 47 -> 47 | 39 |
| 2986 | A | `bazzar` | `bazaar` | +0 | 45 -> 45 | 45 -> 45 | 15 |
| 3123 | A | `daugher` | `daughter` | +1 | 60 -> 61 | 60 -> 61 | 29 |
| 3152 | B | `adpot` | `adopt` | +0 | 16 -> 16 | 24 -> 24 | - |
| 3471 | A | `yown` | `town` | +0 | 70 -> 70 | 70 -> 70 | 165 |
| 3480 | B | `alot` | `a lot` | +1 | 25 -> 26 | 25 -> 26 | - |
| 3528 | A | `Riedock` | `Reidock` | +0 | 44 -> 44 | 44 -> 44 | 116 |
| 3578 | A | `beatiful` | `beautiful` | +1 | 42 -> 43 | 42 -> 43 | 52 |
| 3596 | A | `stange` | `strange` | +1 | 11 -> 12 | 33 -> 34 | 38 |
| 3651 | B | `thiefs` | `thieves` | +1 | 68 -> 69 | 68 -> 69 | - |
| 3851 | B | `alot` | `a lot` | +1 | 30 -> 31 | 30 -> 31 | - |
| 4176 | B | `hesistate` | `hesitate` | -1 | 61 -> 60 | 61 -> 60 | - |
| 4202 | A | `splendind` | `splendid` | -1 | 23 -> 22 | 23 -> 22 | 11 |
| 4324 | A | `tring` | `trying` | +1 | 46 -> 47 | 46 -> 47 | 20 |
| 4462 | A | `amoung` | `among` | -1 | 56 -> 55 | 56 -> 55 | 2 |
| 4583 | A | `Poseiden` | `Poseidon` | +0 | 45 -> 45 | 45 -> 45 | 5 |
| 4648 | A | `kow` | `know` | +1 | 63 -> 64 | 63 -> 64 | 217 |
| 4664 | A | `abscense` | `absence` | -1 | 61 -> 60 | 61 -> 60 | 1 |
| 4675 | A | `Ths` | `The` | +0 | 54 -> 54 | 54 -> 54 | 3712 |
| 4719 | B | `alot` | `a lot` | +1 | 12 -> 13 | 50 -> 51 | - |
| 4928 | A | `stange` | `strange` | +1 | 55 -> 56 | 55 -> 56 | 38 |
| 4950 | A | `incantaion` | `incantation` | +1 | 53 -> 54 | 53 -> 54 | 2 |
| 5070 | B | `disiplined` | `disciplined` | +1 | 41 -> 42 | 41 -> 42 | - |
| 5098 | A | `Baptimsal` | `Baptismal` | +0 | 37 -> 37 | 37 -> 37 | 11 |
| 5099 | A | `Baptimsal` | `Baptismal` | +0 | 47 -> 47 | 47 -> 47 | 11 |
| 5132 | B | `embarassed` | `embarrassed` | +1 | 48 -> 49 | 48 -> 49 | - |
| 5304 | A | `botton` | `bottom` | +0 | 54 -> 54 | 54 -> 54 | 14 |
| 5894 | A | `frm` | `from` | +1 | 34 -> 35 | 34 -> 35 | 237 |
| 6076 *(internal)* | A | `aquired` | `acquired` | +1 | 20 -> 21 | 20 -> 21 | 18 |
| 6146 *(internal)* | A | `caslte` | `castle` | +0 | 37 -> 37 | 37 -> 37 | 220 |
| 6551 | B | `alot` | `a lot` | +1 | 12 -> 13 | 12 -> 13 | - |
| 6761 | A | `existance` | `existence` | +0 | 48 -> 48 | 48 -> 48 | 1 |
| 6812 | A | `Eveyone` | `Everyone` | +1 | 43 -> 44 | 43 -> 44 | 87 |
| 6892 | A | `relly` | `really` | +1 | 52 -> 53 | 52 -> 53 | 216 |
| 6930 | A | `Excellect` | `Excellent` | +0 | 17 -> 17 | 22 -> 22 | 2 |

### In context

**31** `Stength` -> `Strength`  
> {D3} received the Stength Seed.

**64** `wimpering` -> `whimpering`  
> *wimpering*

**155** `aquired` -> `acquired`  
> {D3} has aquired the flying bed.

**191** `forunate` -> `fortunate`  
> ...r answers. //  / {D4}Priest{SPK}John was very forunate to have loving parents like you. //...

**239** `penninsula` -> `peninsula`  
> ...floating island near the western penninsula?

**248** `penninsula` -> `peninsula`  
> ...of Happiness is near the western penninsula.

**296** `Mahamen` -> `Mahamed`  
> ...ke a name! Moore, or something! //  / {D4}Mahamen{SPK}Who could he have been refering t...

**296** `refering` -> `referring`  
> ...//  / {D4}Mahamen{SPK}Who could he have been refering to?

**339** `probaly` -> `probably`  
> ...le to use it. //  / Of course, {CC} could probaly manage.

**361** `porportional` -> `proportional`  
> ...t is a spell that inflicts damage porportional to the energy put into it. //  / Howev...

**374** `decendant` -> `descendant`  
> ...s the new elder. //  / {D4}Mrs.Calbe{SPK}As a decendant of the sorceress, it is your obli...

**380** `convient` -> `convenient`  
> ...es. //  / {D4}Mr.Calbe{SPK}It is an extremely convient form of travel.

**393** `in in` -> `in`  
> ...you think it's okay to just barge in in like that?

**409** `Theather` -> `Theatre`  
> ...le paradise. Welcome to the Bunny Theather.

**554** `suprise` -> `surprise`  
> Don't suprise me like that. You're as bad as Mu...

**658** `I'l` -> `I'll`  
> {D4}Mitchell{SPK}I'l be waiting.

**829** `wimpering` -> `whimpering`  
> {D4}Silver{SPK}.? / *wimpering*

**874** `Unfiorms` -> `Uniforms`  
> {D3} received 4 Soldier's Unfiorms.

**966** `Tommorow` -> `Tomorrow`  
> {D4}Gon{SPK}Eh? Tommorow? Anna? I don't believe it. //  / {D4}Gon{SPK}...

**1003** `siezed` -> `seized`  
> Their key and uniforms / siezed, {D3}'s party /  was imprisoned again!

**1044** `occured` -> `occurred`  
> ...thought our revolution would have occured sooner, but! //  / {D4}Tonra{SPK}Since none o...

**1093** `alot` -> `a lot`  
> .... //  / It's all because of you. Thanks alot.

**1202** `did't` -> `didn't`  
> .... //  / He's fighting a big monster. //  / I did't want to get hurt, so I came back...

**1228** `embarrasing` -> `embarrassing`  
> ...n is on a difficult journey. //  / It's embarrasing, but I'm looking for a lost dream...

**1258** `persistant` -> `persistent`  
> {D4}Rob{SPK}You're those persistant people from before. //  / {D4}Rob{SPK}Why won...

**1389** `basptism` -> `baptism`  
> The basptism is complete. I can do nothing mor...

**1440** `jounrey` -> `journey`  
> ...rough the tunnel. //  / I'll finish my jounrey after I get a little rest.

**1493** `devestation` -> `devastation`  
> ...become /        more powerful, /   my devestation grows.

**1549** `somwhere` -> `somewhere`  
> Hmmm! / Haven't I seen you somwhere before?

**1606** `inconvient` -> `inconvenient`  
> ...o has being invisible been at all inconvient for you?

**1701** `yous` -> `you`  
> ...gladly reward you for the medals yous bring me.

**1712** `yous` -> `you`  
> ...gladly reward you for the medals yous bring me.

**1779** `stength` -> `strength`  
> ...e. //  / However, the second time your stength and magic are weakened. //  / It's real...

**1821** `wher` -> `where`  
> This is wher you pick up prizes. //  / I'm going to...

**1888** `the the` -> `the`  
> I helped build the the slime arena, even this house. //  / Bu...

**1973** `refering` -> `referring`  
> ...ver for him? //  / I wonder who was he refering to when he died? //  / I hope I never...

**2278** `Congradulations` -> `Congratulations`  
> Congradulations on making it this far. I am the f...

**2543** `Foribidden` -> `Forbidden`  
> ...dancer? //  / Do you want to learn the Foribidden dance?

**2663** `enegergetic` -> `energetic`  
> ...getic as usual. //  / {D4}Tania{SPK}Even more enegergetic. It's hard to believe. //  / {D4}Tania{SPK}I f...

**2679** `Riedock` -> `Reidock`  
> ...u're done working as a soldier at Riedock?

**2820** `choise` -> `choice`  
> {DB}That's a wise choise. Now let me deal with the real yo...

**2892** `stroy` -> `story`  
> There's a stroy being passed around the castle. //  /...

**2986** `bazzar` -> `bazaar`  
> {D4}Doga{SPK}This year's bazzar was quite profitable. //  / {D4}Doga{SPK}Surp...

**3123** `daugher` -> `daughter`  
> I've been waiting for you. My daugher told me what happened. //

**3152** `adpot` -> `adopt`  
> Really!? / Can I adpot you?

**3471** `yown` -> `town`  
> Welcome back. The mayor left yown. Would you like to be the new may...

**3480** `alot` -> `a lot`  
> It was you.? Thanks alot.

**3528** `Riedock` -> `Reidock`  
> The king and queen of Riedock have awakened! //  / So my pookie has...

**3578** `beatiful` -> `beautiful`  
> ...of treasure. //  / I think Gina was as beatiful as a goddess.

**3596** `stange` -> `strange`  
> How stange! / Where'd you come from? //  / I don't...

**3651** `thiefs` -> `thieves`  
> Long ago, two thiefs went looking for treasure in the...

**3851** `alot` -> `a lot`  
> Thank you, elder. Thanks alot. //

**4176** `hesistate` -> `hesitate`  
> {D4}{CA}{SPK}I would never hesistate to join you under the circumstanc...

**4202** `splendind` -> `splendid`  
> What a splendind horse.

**4324** `tring` -> `trying`  
> I don't understand. What are you tring to say?

**4462** `amoung` -> `among`  
> ...dock! //  / Maybe the king should walk amoung the people more often.

**4583** `Poseiden` -> `Poseidon`  
> King Poseiden lives at the bottom of the sea. //  /...

**4648** `kow` -> `know`  
> ...p my husband. //  / {D4}Shera{SPK}But I don't kow why I became the king in the drea...

**4664** `abscense` -> `absence`  
> ...ream world. //  / {D4}King{SPK}However, in my abscense, the real Mudo has grown strong. //...

**4675** `Ths` -> `The`  
> Ths king is awake. Maybe the red pepp...

**4719** `alot` -> `a lot`  
> ...he ones who defeated Mudo? / Thanks alot.

**4928** `stange` -> `strange`  
> A stange demon appears and seems to be lau...

**4950** `incantaion` -> `incantation`  
> ...I can remove the curse with this incantaion. //  / {D4}King{SPK}!! //

**5070** `disiplined` -> `disciplined`  
> The people think Holse is not disiplined. //  / But he is our child. //  / Someday h...

**5098** `Baptimsal` -> `Baptismal`  
> Don't get lost in the Baptimsal cave.

**5099** `Baptimsal` -> `Baptismal`  
> ...//  / Then the monsters have left the Baptimsal Cave? //

**5132** `embarassed` -> `embarrassed`  
> ...'re probably right. But I'm still embarassed.

**5304** `botton` -> `bottom`  
> .... As different as the sky and the botton of the sea.

**5894** `frm` -> `from`  
> A {B2} appeared frm the ground nearby.

**6076** `aquired` -> `acquired`  
> Broken heart aquired

**6146** `caslte` -> `castle`  
> End Reidock caslte memory trace event

**6551** `alot` -> `a lot`  
> {DE}Thanks alot.

**6761** `existance` -> `existence`  
> ...arl{SPK}I didn't know of this castle's existance. //  / {D4}Masarl{SPK}This is amazing. I'll n...

**6812** `Eveyone` -> `Everyone`  
> Hey {C9}. You've returned. //  / Eveyone is talking about you. Come with m...

**6892** `relly` -> `really`  
> I'm relly happy that you were able to retur...

**6930** `Excellect` -> `Excellent`  
> The {B5}? / Excellect choice. //

### Name table

| ID | tier | shipped | corrected | delta | attested |
|---|:---:|---|---|---:|---:|
| $0328 | B | `Amatuer|Class` | `Amateur|Class` | +0 | - |
| $0354 | A | `Congradulations.` | `Congratulations.` | +0 | 10 |
| $0355 | A | ` coins recieved.` | ` coins received.` | +0 | 47 |

`$0328` is one of eight class labels: Invite, Student, Family, **Amatuer**,
Business, Survival, Expert, Master. The other two are casino strings.

These three are corrected in the **bytes of their own entries**, not by
re-encoding the text. Re-encoding would have been simpler and it would have
been wrong: `$0355` ends on byte `$7A` and the build encoder writes `$7F`.
Both draw a full stop, so nothing would have looked different and a byte of
theirs would have changed for no reason. `tools/verify.py` caught that on the
first build and it is now checked on every build.

## What was found and NOT corrected

The audit that produced the list above found thirteen more candidates. Every
one needs a judgment call somewhere, so every one fails both clauses of the
rule and stays as NoPrgress wrote it. They are recorded here so that nobody
has to find them again, and so that "why did you stop there" has an answer.

| where | shipped | why it is not corrected |
|---|---|---|
| MSG 844 | `the the` | doubled, but deleting one gives `send you the prison`. The sentence wants `to the`, so the fix is a word, not a deletion |
| MSG 6727 | `avante-guarde` | `avant-garde` needs two changes, one of them to a part that is not obviously a slip |
| MSG 796 | `hotspring` | they write `hot spring` once elsewhere, so this is their compound spelling, not clearly an error |
| NT $0634 | `Expell` | Dragon Warrior III spells it `Expel`, but this sits among their own coinages (`Firebal`, `Infermore`, `Blazemost`) and may be house spelling |
| NT $0787 | `Enducing` | a monster-action fragment beside `Blinding`, `Shake`, `Lick`. `Inducing`, `Seducing` and `Enduring` are all readable. Not resolvable without the Japanese |
| NT $0759 | `ToOthers` | a runtime-assembled fragment; its neighbors (`Front of`, `Stand in`) suggest a space belongs, but the assembly order is untraced |
| NT $037E | `Terrys Sister` | missing apostrophe; `Terry's` is attested once, but an apostrophe is punctuation and punctuation is out of scope |
| NT $0304 | `Holidy` | a boss name. `Holiday` is plausible and these lists are full of deliberate coinages |
| NT $093A | `Cloun` | a companion name; `Clown` is plausible, same problem |
| NT $091E | `Sadow` | a companion name; `Shadow` is plausible, same problem |
| NT $093B | `Kdngle` | a companion name with no reading at all |
| NT $0830 | `Calbero Boot` | beside the town `Calberona`. Ambiguous |
| NT $0853 | `Sword of Ramias` | against `Ramia's Sword` in messages 4876, 5982 and 6141. An inconsistency between two of their own forms, not a misspelling |

Punctuation is excluded as a class, and that exclusion is doing real work:
their script uses symbol `$0246` 2,473 times where a comma or an ellipsis
would be expected. Not one of those is touched.

