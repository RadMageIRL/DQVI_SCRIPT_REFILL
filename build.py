#!/usr/bin/env python3
"""
Build the DQ6 Script Refill ROM from a stock NoPrgress ROM.

This is the script that produced the released patch. It is published so the
build is reproducible and so anyone can see exactly what is written where.

  usage:  build.py <noprgress.sfc> <candidates-en.txt> <nametable-en.txt> <out.sfc>

Everything it needs is either in this repository or in this file, so a stock
NoPrgress ROM plus the two text files reproduces the released ROM. Nothing is
fetched from anywhere else.

It does seven things:
  1. applies both crash fixes, Info > All and Forget (see apply_crash_fixes)
  2. restores the gold window on the info screen (see apply_gold below)
  3. writes the 184 name-table entries (see apply_names below)
  4. decodes all 6,960 messages from the unmodified payload
  5. substitutes the 421 authored English messages
  6. removes the redundant speech marker, all 676 occurrences of a symbol
     with no English glyph (see drop_speech_marker below)
  7. re-encodes every message with the ROM'S EXISTING Huffman trees, rebuilds
     the 870-entry pointer table, and recomputes the internal checksum

The trees are never modified. Every symbol already has exactly one code path in
them, so the encode is deterministic: every message comes out symbol for symbol
as NoPrgress wrote it, apart from the 421 that were never written and one
marker symbol removed wherever it appeared. **Their dialogue is untouched.**
That property is worth checking after any change to this script, and
tools/verify.py checks it: it fails if any symbol other than that marker moves
in any of their messages.

One NAME-TABLE entry of theirs is changed, $070B, and the rule that permits it
is narrow: their text is changed only where their rendering blocks completing an
untranslated entry. See the README. It does not apply to the message script,
where nothing of theirs is altered at all.

Message system, decoded from the ROM at $C0:2B69 onward:
  - Pointer table at $C1:5BB5, 870 entries of 3 bytes, indexed by (ID >> 3).
    Each entry heads a run of 8 messages, so the ID space is 6,960.
  - entry >> 3 is a byte offset from $F7:175B; entry & 7 is the start bit.
  - Huffman trees at $C1:67BE (bit clear) and $C1:700E (bit set); nodes are
    byte-indexed 16-bit words, MSB-first, bit 15 set = internal node.
  - The tree root is read from the code at $C0:2BFB and differs per ROM.
  - Messages end on $00AC or $00AE and each message keeps its own terminator.

Standard library only. Writes one file, the output ROM.
"""
import io, re, sys, hashlib, zlib

TBL, PAY = 0x015BB5, 0x370000 + 0x175B
T0, T1 = 0x0167BE, 0x01700E
TERM = (0x00AC, 0x00AE)
NAMETBL = 0x011100
GROUPS = 870
HDR = 0x00FFC0
FREE_END = 0x3B874B      # measured: no reads observed in $FB:2133-$FB:874B


class Rom:
    def __init__(self, data):
        self.d = data
        assert self.d[0x2bfa] == 0xA2, 'not a DQ6 ROM: no LDX #imm at $C0:2BFA'
        self.root = self.d[0x2bfb] | (self.d[0x2bfc] << 8)

    def sym(self, b):
        o = NAMETBL + b * 2
        return self.d[o] | (self.d[o + 1] << 8)

    def entry(self, g):
        o = TBL + g * 3
        return self.d[o] | (self.d[o + 1] << 8) | (self.d[o + 2] << 16)

    def decode_all(self):
        """Every message as (symbols, terminator), in ID order."""
        d, out = self.d, []
        for g in range(GROUPS):
            e = self.entry(g)
            A = (e >> 3) * 8 + (7 - (e & 7))
            for _ in range(8):
                syms = []
                while True:
                    x = self.root
                    while True:
                        b = (d[PAY + (A >> 3)] >> (7 - (A & 7))) & 1
                        A += 1
                        base = T1 if b else T0
                        v = d[base + x] | (d[base + x + 1] << 8)
                        if v & 0x8000:
                            x = v & 0x7FFF
                        else:
                            break
                    if v in TERM:
                        break
                    syms.append(v)
                out.append((syms, v))
        return out

    def codes(self):
        """symbol -> bit string, by walking both trees from the root."""
        d, out, stack = self.d, {}, [(self.root, '', frozenset([self.root]))]
        while stack:
            x, pre, seen = stack.pop()
            if len(pre) > 64:
                continue
            for b in (0, 1):
                base = T1 if b else T0
                v = d[base + x] | (d[base + x + 1] << 8)
                if v & 0x8000:
                    nx = v & 0x7FFF
                    if nx not in seen:
                        stack.append((nx, pre + str(b), seen | {nx}))
                elif v not in out:
                    out[v] = pre + str(b)
        return out


class BitWriter:
    def __init__(self):
        self.by, self.n = bytearray(), 0

    def put(self, bits):
        for c in bits:
            if self.n % 8 == 0:
                self.by.append(0)
            if c == '1':
                self.by[-1] |= 1 << (7 - (self.n % 8))
            self.n += 1



# ---------------------------------------------------------------------------
# The gold window on the info screen
#
# NoPrgress widened the status window to fit English stat labels and moved the
# gold window underneath it:
#
#     Japanese   status cols 10-21   gold cols 22-30    no overlap
#     English    status cols 10-24   gold cols 16-23    gold buried
#
# Having no room left for it, they deleted the call that draws the gold "G"
# from the routine at $C3:3593 - seven bytes, `LDA #$007A / JSL $C3763A` - and
# padded the gap with a duplicated RTL epilogue so downstream addresses stayed
# put. The same padding trick appears four bytes earlier in the deleted
# `STA $3AC2` that causes the Info > All crash.
#
# This restores the original behaviour rather than adding anything:
#
#   - the draw call is put back, at exact size, over the English 15 bytes plus
#     the dead duplicate epilogue. No relocation. The write ends at $35A8, one
#     byte short of $35A9, which is the routine that opens the window.
#   - it draws string $10, a bare one-byte "G". Entry $7A is NOT a gold string:
#     $74-$7F are " A" through " L", an alphabet series where every entry
#     carries an $88 prefix, and that prefix renders as a stray mark. $10 is
#     what NoPrgress point their OTHER gold window at, so this is their own
#     substitution applied to the site they missed.
#   - the window moves to cols 1-9, rows 1-3, where the English layout has
#     room. Only its own descriptor changes; no other window moves.
#
# Window geometry lives in a descriptor table at $C5:7B5C, 14 bytes per entry,
# indexed by $3058. Gold is entry 58; bytes 11-13 of each entry are the draw
# routine pointer, which is how it was identified.

GOLD_CODE_AT = 0x033593
GOLD_CODE_WAS = bytes.fromhex('A93E0022FE83C3ABC2307AFA68286BC2307AFA68286B')
GOLD_CODE_NOW = bytes.fromhex('A91000223A76C3A93E0022FE83C3ABC2307AFA68286B')
GOLD_DESC_AT = 0x057E88          # descriptor 58, bytes 0-2: X, Y, W
GOLD_DESC_NOW = bytes([0x01, 0x01, 0x09])



# ---------------------------------------------------------------------------
# The two crash fixes
#
# Both are the same kind of accident: bytes removed to make room, with the
# surrounding code shuffled so that addresses still lined up. Neither is a
# design decision.
#
# INFO > ALL. A three-byte STA $3AC2 was deleted from $C3:3538. It writes the
# party-slot loop bound; without it the bound keeps a $FF sentinel from the
# previous screen, the loop walks past the end of the party, and the game trips
# an assertion at $C4:560F. The deleted bytes were absorbed by shifting the
# following three back, so nothing after the deletion moved - which is exactly
# what makes it invisible in a byte diff.
#
# The fix restores the 87-byte span, which is the Japanese original for that
# span. It is embedded here rather than copied from a Japanese ROM at build
# time, so no second ROM is needed.
#
# FORGET. Not a logic bug. Every instruction on the fault path is byte-identical
# to the Japanese original; the defect is in WHERE the translation put its data.
# Word-wrap state was placed at $7E:379E / $37A0 / $37A2, inside a 112-byte
# block the original game clears wholesale, so the state is wiped mid-use.
#
# The fix relocates that state to $7E:55BE / $55C0 / $55C2, a region established
# as unused. 19 sites, operands only - no opcode changes and no instruction
# length changes - plus two branch conditions.
#
# Residual risk, stated plainly: the destination was chosen from emulator code
# and data logs, two RAM snapshots, and traces covering field movement,
# dialogue, shops, menus and battle. No logged session covers every context in
# the game, and code that has never executed cannot be ruled out.
#
# Full analysis: docs/CRASH-FIXES.md, and the DQVI_NOPRGRESS_MENU_FIX repo.

CF_SPAN = 0x033538                  # $C3:3538
CF_BEFORE = bytes.fromhex(
    "22257bc3a9870022fe83c3a9260022fe83c3a92c0022fe83c322f975c3a92d00"
    "22fe83c322f975c3a92e0022fe83c322f975c3a92f0022fe83c322f975c3a930"
    "0022fe83c3a98a0022fe83c3abc2307afa68286b68286b")
CF_AFTER = bytes.fromhex(
    "8dc23a22257bc3a9870022fe83c3a9260022fe83c3a92c0022fe83c322f975c3"
    "a92d0022fe83c322f975c3a92e0022fe83c322f975c3a92f0022fe83c322f975"
    "c3a9300022fe83c3a98a0022fe83c3abc2307afa68286b")

CF_WIDTH, CF_LENGTH, CF_BUFFER = 0x55BE, 0x55C0, 0x55C2   # were $379E/$37A0/$37A2

# (file offset of the opcode, opcode, old operand, new operand)
CF_RELOCATIONS = (
    (0x00FDD5, 0x9C, 0x37A0, CF_LENGTH), (0x00FDE0, 0xAE, 0x37A0, CF_LENGTH),
    (0x00FDE8, 0x8E, 0x37A0, CF_LENGTH), (0x00FDFE, 0x8E, 0x37A0, CF_LENGTH),
    (0x00FE24, 0xEC, 0x37A0, CF_LENGTH), (0x00FF03, 0x8E, 0x37A0, CF_LENGTH),
    (0x00FF1A, 0xEC, 0x37A0, CF_LENGTH), (0x00FF1F, 0x9C, 0x37A0, CF_LENGTH),
    (0x00FDE3, 0x9D, 0x37A2, CF_BUFFER), (0x00FE29, 0xBD, 0x37A2, CF_BUFFER),
    (0x00FE69, 0xBD, 0x37A2, CF_BUFFER), (0x00FEF2, 0x9D, 0x37A2, CF_BUFFER),
    (0x00FF22, 0xBD, 0x37A2, CF_BUFFER), (0x00FF34, 0xBD, 0x37A2, CF_BUFFER),
    (0x00FE81, 0x8D, 0x379E, CF_WIDTH),  (0x00FE85, 0xCD, 0x379E, CF_WIDTH),
    (0x00FE8B, 0xED, 0x379E, CF_WIDTH),  (0x00FEA2, 0x8D, 0x379E, CF_WIDTH),
    (0x00FEA7, 0x6D, 0x379E, CF_WIDTH),
)

# (file offset, old opcode, new opcode)
CF_BRANCHES = ((0x00FE27, 0xF0, 0xB0), (0x00FF1D, 0xD0, 0x90))


def apply_crash_fixes(rom):
    """Info > All and Forget. Refuses to write if the ROM is not as expected."""
    found = bytes(rom[CF_SPAN:CF_SPAN + len(CF_BEFORE)])
    if found != CF_BEFORE:
        raise SystemExit(
            'crash fix: the span at 0x%06X is not the expected pre-fix bytes.\n'
            '  expected %s\n  found    %s\n  Refusing to write.'
            % (CF_SPAN, CF_BEFORE.hex(), found.hex()))
    for off, opcode, old, _new in CF_RELOCATIONS:
        if rom[off] != opcode or (rom[off + 1] | rom[off + 2] << 8) != old:
            raise SystemExit('crash fix: site 0x%06X is not as expected' % off)
    for off, old, _new in CF_BRANCHES:
        if rom[off] != old:
            raise SystemExit('crash fix: branch 0x%06X is not as expected' % off)

    rom[CF_SPAN:CF_SPAN + len(CF_AFTER)] = CF_AFTER
    for off, _opcode, _old, new in CF_RELOCATIONS:
        rom[off + 1] = new & 0xFF
        rom[off + 2] = (new >> 8) & 0xFF
    for off, _old, new in CF_BRANCHES:
        rom[off] = new
    return len(CF_RELOCATIONS) + len(CF_BRANCHES)


def apply_gold(rom):
    """Restore the gold window. Refuses to run if the ROM is not as expected."""
    n = len(GOLD_CODE_WAS)
    if bytes(rom[GOLD_CODE_AT:GOLD_CODE_AT + n]) != GOLD_CODE_WAS:
        raise SystemExit('gold: code at 0x%06X is not the expected English form'
                         % GOLD_CODE_AT)
    rom[GOLD_CODE_AT:GOLD_CODE_AT + len(GOLD_CODE_NOW)] = GOLD_CODE_NOW
    rom[GOLD_DESC_AT:GOLD_DESC_AT + 3] = GOLD_DESC_NOW
    return len(GOLD_CODE_NOW) + 3



# ---------------------------------------------------------------------------
# The name table
#
# Item, spell, skill, place, monster-action and menu strings live in a second
# system entirely separate from the Huffman message script: byte-encoded,
# $AC-terminated, packed end to end from $FB:8703.
#
# It is addressed indirectly. The routine at $C0:315E splits a string ID as
#
#     group = ID >> 4          low = ID & 0x0F
#
# reads a 24-bit offset from the group table at $C1:65E7 (3 bytes per group),
# adds $FB8703 with carry, then walks `low` $AC terminators forward. Entries
# within a group are therefore found POSITIONALLY, so changing the length of
# any entry moves every entry after it.
#
# This repacks the whole table and regenerates all 157 group offsets, which is
# what allows the authored entries to be longer than the identifiers they
# replace. 28 groups deliberately share a base with the group before them -
# collapsed ranges of unused IDs - and that aliasing is preserved exactly.
#
# Two things about the byte encoding are not obvious and both produced bugs:
#
#   - Bytes $0C-$0F SHADOW the ordinary letters H, M, P and G in the
#     byte-to-symbol table, but they are renderer control codes rather than
#     glyphs; $0D draws a tilde. Encoding "M" as $0D yields "~adante 2".
#     H, M, P and G must use $17, $1C, $1F and $16.
#   - A line break is 0x90 plus the length of the line before it. Verified
#     against every multi-line entry in the stock table: Ice/Breath $93,
#     Slime/Behemoth $95, Octopus/Jar Boy $97, Scorching/Breath $99,
#     Metal King/Slime $9A, Moon Folding/Fan $9C, Spotted Slime/Boss $9D.

NT_PTR = 0x0165E7          # $C1:65E7, 3 bytes per group of 16 IDs
NT_BASE = 0x3B8703         # string ID 0
NT_END = 0x3BC712          # end of the region; past the live table is the
                           # dead Japanese remnant, byte-identical to the JP ROM
NT_GROUPS = 157            # groups 0..156, IDs 0..2511


# A deliberately empty entry is written as <blank> rather than as an empty
# field. Two reasons, both learned the hard way here. The row regex requires a
# non-space character, so a row with nothing after the ID does not match and is
# SILENTLY SKIPPED - the build would report the entry written and leave it
# untouched. And trailing whitespace is invisible and gets stripped by editors,
# so a format that depends on it cannot survive being edited. "<" has no glyph
# in this charset and cannot be encoded, so the sentinel can never collide with
# real text.
#
# Blanking is the translation's own convention for a string English does not
# express: 75 of their entries are empty where the Japanese has content, and no
# Japanese entry is empty. $00F5 is the animal counter, and their $0324 is the
# counter for flat objects, which they blanked.
BLANK = '<blank>'


def read_nametable(path):
    """Parse '<hex id>  <english>' rows. <blank> means a deliberately empty
    entry."""
    out = {}
    for line in io.open(path, encoding='utf-8'):
        m = re.match(r'^([0-9A-Fa-f]{4})\s\s+(\S.*?)\s*$', line)
        if m:
            text = m.group(2)
            out[int(m.group(1), 16)] = '' if text == BLANK else text
    if not out:
        raise SystemExit('no name-table rows in %s' % path)
    return out


# ---------------------------------------------------------------------------
# The dictionary
#
# Name-table bytes at or above $C9 are dictionary codes, each drawing a short
# fixed sequence. v1.0 shipped a table of these reconstructed from decoded
# output, and ten of the fifty entries were wrong. They were wrong in one
# direction and for one reason: a sequence that begins or ends with a SPACE
# still reads as fluent English when the space is dropped. "Mudo'" + $F2 +
# "Castle" rendered as "Mudo'sCastle", which passes for a packing quirk rather
# than a decoding error, and so it was never questioned.
#
# There is no need to reconstruct any of it. The expander at $C3:FB23 reads:
#
#     CMP #$00C9          the lowest dictionary code
#     BCC ...             below that, not a dictionary code at all
#     SBC #$00C9
#     ASL / TAX
#     LDA $C3FB50,X       first byte of the pair
#     LDA $C3FB51,X       second byte
#
# so the lowest code, the table address and the entry width are all readable
# out of the instructions, and $FF terminates the table. Read that way the
# dictionary cannot drift from what the game actually draws. A reconstruction
# always can, and this one did.
#
# $C8 is NOT a dictionary code despite sitting next to them. It occurs in four
# dead name-entry grid slots and nowhere the game draws.

DICT_CMP = 0x03FB25        # operand of the CMP #imm that bounds the range
DICT_PTR = 0x03FB30        # operand of the LDA long that indexes the table


def read_dictionary(rom):
    """code -> the text it draws, read out of the ROM's own expander."""
    first = rom[DICT_CMP] | rom[DICT_CMP + 1] << 8
    base = (rom[DICT_PTR] | rom[DICT_PTR + 1] << 8
            | (rom[DICT_PTR + 2] & 0x3F) << 16)
    if not 0xC0 <= first <= 0xFF or not 0 < base < len(rom) - 128:
        raise SystemExit('the dictionary expander at 0x%06X is not what this '
                         'build expects.\n  Refusing to guess.' % DICT_CMP)
    out, i = {}, 0
    while rom[base + i * 2] != 0xFF:
        out[first + i] = (rom[base + i * 2], rom[base + i * 2 + 1])
        i += 1
        if i > 64:
            raise SystemExit('the dictionary table at 0x%06X does not '
                             'terminate.' % base)
    return out


def _nt_encoder(rom):
    inv = {}
    for i, c in enumerate('0123456789'):
        inv[c] = 0x02 + i
    for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        inv[c] = 0x10 + i              # NOT $0C-$0F, which shadow H, M, P, G
    for i, c in enumerate('abcdefghijklmnopqrstuvwxyz'):
        inv[c] = 0x42 + i
    inv[' '] = 0x01
    # Punctuation, read out of the charset table rather than assumed. Note $85
    # and $80 both draw the label colon (their "Level:", "Sex:", "Max HP:"),
    # and $7A and $7F both draw a full stop.
    inv["'"] = 0x77
    inv['-'] = 0x78
    inv['?'] = 0x79
    inv['.'] = 0x7F
    inv[':'] = 0x85
    inv['!'] = 0x81
    inv['*'] = 0x89
    inv[','] = 0x8B
    # $0D is a renderer control code that draws a tilde, not a charset index;
    # it is what their own "~30HP to" and "~80HP to" use.
    inv['~'] = 0x0D
    # The dictionary, read out of the ROM. Every code expands to two bytes
    # that are themselves ordinary charset indices, so naming them uses the
    # same map as everything else and nothing here is reconstructed.
    letter = dict((b, c) for c, b in inv.items())
    letter[0x7A] = '.'                 # $7A and $7F both draw a full stop
    lig = {}
    for code, (a, b) in sorted(read_dictionary(rom).items()):
        if a not in letter or b not in letter:
            raise SystemExit('dictionary code $%02X expands to bytes this '
                             'build cannot name (%02X %02X).' % (code, a, b))
        lig.setdefault(letter[a] + letter[b], code)
    return inv, lig


def _nt_encode(text, inv, lig):
    out, k, n = [], 0, 0
    order = sorted(lig, key=len, reverse=True)
    while k < len(text):
        if text[k] == '|':
            if not 1 <= n <= 13:
                raise SystemExit('line of %d cannot carry a break: %r' % (n, text))
            out.append(0x90 + n); n = 0; k += 1; continue
        for t in order:
            if text.startswith(t, k):
                out.append(lig[t]); k += len(t); n += len(t); break
        else:
            if text[k] not in inv:
                raise SystemExit('cannot encode %r in %r' % (text[k], text))
            out.append(inv[text[k]]); k += 1; n += 1
    return bytes(out)


def apply_names(rom, table):
    """Write the authored entries and regenerate the group offsets."""
    inv, lig = _nt_encoder(rom)
    entries, s = [], NT_BASE
    for i in range(NT_BASE, NT_END):
        if rom[i] == 0xAC:
            entries.append(bytes(rom[s:i])); s = i + 1
    start_of, p = {}, NT_BASE
    for n, e in enumerate(entries):
        start_of[p] = n; p += len(e) + 1

    groups = []
    for g in range(NT_GROUPS):
        o = NT_PTR + g * 3
        raw = rom[o] | rom[o + 1] << 8 | rom[o + 2] << 16
        a = (0xFB8703 + raw) & 0xFFFFFF
        groups.append(start_of[((a >> 16) & 0x3F) << 16 | (a & 0xFFFF)])
    live_end = max(groups) + 15

    pos_of = {}
    for idv in range(NT_GROUPS * 16):
        pos_of.setdefault(groups[idv >> 4] + (idv & 0x0F), idv)
    id_pos = {}
    for pos, idv in pos_of.items():
        id_pos[idv] = pos

    for idv, text in table.items():
        if idv not in id_pos:
            raise SystemExit('string ID $%04X is not reachable' % idv)
        entries[id_pos[idv]] = _nt_encode(text, inv, lig)

    src_end = NT_BASE
    for e in entries[:live_end + 1]:
        src_end += len(e) + 1
    tail = bytes(rom[src_end:NT_END])
    packed, new_start = bytearray(), []
    for e in entries[:live_end + 1]:
        new_start.append(NT_BASE + len(packed))
        packed += e + b'\xAC'
    if NT_BASE + len(packed) + len(tail) > NT_END:
        raise SystemExit('repacked name table overruns 0x%06X' % NT_END)
    rom[NT_BASE:NT_BASE + len(packed)] = packed
    rom[NT_BASE + len(packed):NT_BASE + len(packed) + len(tail)] = tail
    end = NT_BASE + len(packed) + len(tail)
    if end < NT_END:
        rom[end:NT_END] = b'\xFF' * (NT_END - end)
    for g, pos in enumerate(groups):
        off = new_start[pos] - NT_BASE
        o = NT_PTR + g * 3
        rom[o], rom[o + 1], rom[o + 2] = off & 0xFF, (off >> 8) & 0xFF, (off >> 16) & 0xFF
    return len(table)



# ---------------------------------------------------------------------------
# The speech marker
#
# The engine draws the opening mark on NPC dialogue itself - a star and a
# bracket before the first word - and it does so in every box that carries
# speech, including shop and service windows. That is confirmed on screen, not
# inferred: an untagged villager and a shop clerk both draw it with nothing in
# the message data asking for one.
#
# NoPrgress additionally wrote symbol $0559 into the script 676 times. $0559 is
# the one symbol in their script with no English glyph behind it, so everywhere
# it appears it draws a stray two-part mark, and everywhere it appears the
# engine has already drawn the real one. It is redundant and broken in every
# position:
#
#     534  opening a message
#     115  after $0240, the opening quote inside a tagged line
#      25  after a context control code
#       2  in the trailing filler past the last real message
#
# Those are counted here, after the 421 authored messages are substituted in,
# which is what this function actually sees. Their script alone opens 519
# messages on it; 3 of those sit in placeholder messages that get replaced, and
# the authored text supplies 18 openings of its own, so 519 - 3 + 18 = 534.
# docs/METHOD.md quotes the 519 because it describes their script.
#
# So it is removed outright rather than replaced. What is left is the engine's
# own marker, which is the Japanese layout.
#
# Two readings were tried and discarded on the way here, both recorded in
# docs/METHOD.md because the wrong ones are the instructive part:
#
#   - that $0559 drew the whole mark, so substituting the plain asterisk $0247
#     would preserve it. It produced a visible double star.
#   - that the 20 openings whose JAPANESE counterpart carries an explicit
#     marker pair ($0511 $0577, the shop-clerk block and the authored lines
#     beside it) needed that mark kept, since the source spells it out there.
#     They do not. The engine draws it in those boxes too.
#
# Both were settled by looking at the game, and neither was settleable without.

MARKER = 0x0559


def drop_speech_marker(msgs):
    """Remove the marker everywhere. It draws nothing readable in any position."""
    n = 0
    for i, (syms, term) in enumerate(msgs):
        if MARKER in syms:
            n += sum(1 for s in syms if s == MARKER)
            msgs[i] = ([s for s in syms if s != MARKER], term)
    return n


REC = re.compile(r'^---- (\d+)$')
TOKEN = re.compile(r'\{([0-9A-Z]{2,4})\}')
# notation used in the candidates file for two symbols with no ASCII equivalent
NOTATION = {'SPK': 0x240, 'STAR': 0x559}


def read_candidates(path):
    """Parse candidates-en.txt back into {id: text}.

    The emitted format uses fixed-width prefixes so this is exactly reversible,
    including leading spaces inside a message, which at least one message
    deliberately has. Do not strip() here: that silently ate an indent the
    first time this was written.
        "  "        starts a message body
        "     | "   a page break, then the rest of the line
        "     / "   a line break, then the rest of the line
    """
    out, cur, buf = {}, None, []

    def flush():
        if cur is not None:
            out[cur] = ''.join(buf)

    for raw in io.open(path, encoding='utf-8'):
        line = raw.rstrip('\r\n')
        m = REC.match(line.strip())
        if m:
            flush()
            cur, buf = int(m.group(1)), []
            continue
        if cur is None:
            continue
        if line.startswith('  -- '):          # a note, not content
            continue
        if not line.strip():                  # blank line ends the record
            flush()
            cur, buf = None, []
            continue
        if line.startswith('     | '):
            buf.append('{AF}' + line[7:])
        elif line.startswith('     / '):
            buf.append('{AD}' + line[7:])
        elif line.rstrip() == '     |':
            buf.append('{AF}')
        elif line.rstrip() == '     /':
            buf.append('{AD}')
        elif line.startswith('  '):
            buf.append(line[2:])
    flush()
    return out


def main(src, cand, names_path, dst):
    rom = bytearray(io.open(src, 'rb').read())
    src_crc = zlib.crc32(bytes(rom)) & 0xFFFFFFFF
    print('source ROM: %d bytes, CRC32 %08X' % (len(rom), src_crc))

    n = apply_crash_fixes(rom)
    print('crash fixes applied: Info > All, and Forget across %d sites' % n)

    g = apply_gold(rom)
    print('gold window restored: %d bytes' % g)

    n_names = apply_names(rom, read_nametable(names_path))
    print('name-table entries written: %d' % n_names)

    r = Rom(bytes(io.open(src, 'rb').read()))
    msgs = r.decode_all()
    codes = r.codes()
    print('decoded %d messages; %d symbols are encodable in this ROM' % (len(msgs), len(codes)))

    inv = {}
    for i, b in enumerate(range(0x02, 0x0C)):
        inv.setdefault('0123456789'[i], r.sym(b))
    for i, b in enumerate(range(0x10, 0x2A)):
        inv.setdefault('ABCDEFGHIJKLMNOPQRSTUVWXYZ'[i], r.sym(b))
    for i, b in enumerate(range(0x42, 0x5C)):
        inv.setdefault('abcdefghijklmnopqrstuvwxyz'[i], r.sym(b))
    inv.setdefault("'", r.sym(0x77))
    inv[' '] = 0x200
    for ch, s in (('.', 0x242), (',', 0x243), ('!', 0x246), ('?', 0x228),
                  ('*', 0x247), ('-', 0x236)):
        inv[ch] = s
    # The font carries a single glyph for "'s". NoPrgress use it throughout, so
    # matching it greedily is what keeps the encode identical to theirs and
    # costs a few hundred bytes less than spelling it out.
    LIGATURE = ("'s", 0x24D)

    def encode(t, mid):
        out, k = [], 0
        while k < len(t):
            m = TOKEN.match(t, k)
            if m:
                nm = m.group(1)
                out.append(NOTATION[nm] if nm in NOTATION else int(nm, 16))
                k = m.end(); continue
            if t[k:k + len(LIGATURE[0])] == LIGATURE[0]:
                out.append(LIGATURE[1]); k += len(LIGATURE[0]); continue
            ch = t[k]
            if ch not in inv:
                raise SystemExit('message %d: cannot encode %r' % (mid, ch))
            out.append(inv[ch]); k += 1
        return out

    C = read_candidates(cand)
    for mid, text in C.items():
        msgs[mid] = (encode(text, mid), msgs[mid][1])
    print('messages substituted: %d' % len(C))

    n_marker = drop_speech_marker(msgs)
    print('redundant speech marker $%04X removed: %d occurrences'
          % (MARKER, n_marker))

    w = BitWriter()
    starts = []
    for g in range(GROUPS):
        starts.append(w.n)
        for k in range(8):
            syms, term = msgs[g * 8 + k]
            for s in syms:
                w.put(codes[s])
            w.put(codes[term])
    payload = bytes(w.by)
    end = PAY + len(payload)
    print('payload: %d bytes, ends at 0x%06X, headroom %d bytes'
          % (len(payload), end, FREE_END - end))
    if end >= FREE_END:
        raise SystemExit('payload overruns the free region')

    rom[PAY:PAY + len(payload)] = payload
    for g in range(GROUPS):
        A = starts[g]
        e = ((A // 8) << 3) | (7 - (A % 8))
        o = TBL + g * 3
        rom[o], rom[o + 1], rom[o + 2] = e & 0xFF, (e >> 8) & 0xFF, (e >> 16) & 0xFF

    rom[HDR + 0x1C:HDR + 0x1E] = b'\xFF\xFF'
    rom[HDR + 0x1E:HDR + 0x20] = b'\x00\x00'
    ck = sum(rom) & 0xFFFF
    rom[HDR + 0x1C:HDR + 0x1E] = bytes([(ck ^ 0xFFFF) & 0xFF, ((ck ^ 0xFFFF) >> 8) & 0xFF])
    rom[HDR + 0x1E:HDR + 0x20] = bytes([ck & 0xFF, (ck >> 8) & 0xFF])

    out = bytes(rom)
    io.open(dst, 'wb').write(out)
    print()
    print('wrote %s' % dst)
    print('  size  %d bytes' % len(out))
    print('  CRC32 %08X' % (zlib.crc32(out) & 0xFFFFFFFF))
    print('  SHA-1 %s' % hashlib.sha1(out).hexdigest())


if __name__ == '__main__':
    if len(sys.argv) != 5:
        print(__doc__.strip().split('\n\n')[1])
        sys.exit(2)
    main(*sys.argv[1:])
