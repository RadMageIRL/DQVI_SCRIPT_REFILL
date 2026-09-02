#!/usr/bin/env python3
"""Check a patched DQ6 ROM against the one it was built from.

  usage:  verify.py <stock NoPrgress.sfc> <patched.sfc>

You supply both ROMs. Nothing else is needed and nothing is written.

This is the verification the README claims, run against two files rather than
quoted. It checks eight things:

  1. NoPrgress's wording is unchanged. Their messages are allowed to differ in
     exactly two ways, the redundant marker being removed and a LISTED
     misspelling being corrected, and the check fails if any other symbol in
     any of them moves. This covers the MESSAGE SCRIPT
  2. the spelling corrections are at the listed sites and nowhere else, split
     into player-facing and internal
  3. every tier-A correction is attested in their own text, resolved in the
     STOCK ROM. This is the spelling rule itself, checked rather than claimed
  4. no message still displays its own ID
  5. every one of the 2,512 name-table string IDs resolves the way the game
     resolves it, in both ROMs, and the two are compared, including the three
     misspellings corrected there
  6. both crash fixes are present at every site they touch
  7. the gold window's draw call and descriptor are in place
  8. the header still says what it said, and the internal checksum agrees

Point 5 is the one that matters most and the one a byte diff cannot do. The
name table is repacked wholesale, so almost every byte in it moves; comparing
bytes tells you nothing at all. Resolving IDs tells you what changed on screen.

Standard-library Python 3 only. No dependencies, nothing to install.
"""
import io
import os
import re
import sys
import zlib

# --- the message script -----------------------------------------------------
ROOT_AT = 0x002BFB
TREE0, TREE1 = 0x0167BE, 0x01700E
TABLE = 0x015BB5
PAYLOAD = 0x37175B
BYTETBL = 0x011100
GROUPS, PER_GROUP = 870, 8
TERMINATORS = (0x00AC, 0x00AE)
GLYPH = 0x0200

# --- the name table ---------------------------------------------------------
NT_PTR = 0x0165E7
NT_BASE = 0x3B8703
NT_END = 0x3BC712
NT_GROUPS = 157
NT_TERM = 0xAC

# --- the two crash fixes ----------------------------------------------------
CF_SPAN = 0x033538
CF_AFTER = bytes.fromhex(
    "8dc23a22257bc3a9870022fe83c3a9260022fe83c3a92c0022fe83c322f975c3"
    "a92d0022fe83c322f975c3a92e0022fe83c322f975c3a92f0022fe83c322f975"
    "c3a9300022fe83c3a98a0022fe83c3abc2307afa68286b")
CF_WIDTH, CF_LENGTH, CF_BUFFER = 0x55BE, 0x55C0, 0x55C2
CF_RELOCATIONS = (
    (0x00FDD5, CF_LENGTH), (0x00FDE0, CF_LENGTH), (0x00FDE8, CF_LENGTH),
    (0x00FDFE, CF_LENGTH), (0x00FE24, CF_LENGTH), (0x00FF03, CF_LENGTH),
    (0x00FF1A, CF_LENGTH), (0x00FF1F, CF_LENGTH), (0x00FDE3, CF_BUFFER),
    (0x00FE29, CF_BUFFER), (0x00FE69, CF_BUFFER), (0x00FEF2, CF_BUFFER),
    (0x00FF22, CF_BUFFER), (0x00FF34, CF_BUFFER), (0x00FE81, CF_WIDTH),
    (0x00FE85, CF_WIDTH), (0x00FE8B, CF_WIDTH), (0x00FEA2, CF_WIDTH),
    (0x00FEA7, CF_WIDTH))
CF_BRANCHES = ((0x00FE27, 0xB0), (0x00FF1D, 0x90))

# --- the gold window --------------------------------------------------------
GOLD_CODE_AT = 0x033593
GOLD_CODE_NOW = bytes.fromhex('A91000223A76C3A93E0022FE83C3ABC2307AFA68286B')
GOLD_DESC_AT = 0x057E88
GOLD_DESC_NOW = bytes([0x01, 0x01, 0x09])

# The animal counter. English has no counter words, so this entry is written
# empty, which is the translation's own convention: 75 of their entries are
# blank where the Japanese has content and none of the Japanese ones are.
COUNTER_ID = 0x00F5

HDR = 0x00FFC0

# The redundant speech marker. The engine draws the real mark itself in every
# box that carries speech; $0559 is the one symbol in their script with no
# English glyph behind it, and it is removed wherever it appears.
MARKER = 0x0559

# --- their spelling ---------------------------------------------------------
#
# The 67 corrections, restated here INDEPENDENTLY of build.py. The duplication
# is deliberate and it is the point: this file and the build state the same
# claim separately, so if one is edited and the other is not, verification
# fails rather than agreeing with itself. Do not import the list from build.py.
#
# Tier A means the ROM attests the corrected spelling elsewhere in their own
# writing. That is checked below against the STOCK ROM, not asserted: if an
# attestation a correction rests on is not there, this fails.
# Tier B means the shipped form is not an English word and has exactly one
# English spelling, so there is nothing of theirs to attest and none is
# required.
TYPOS = (
    ('Ths', 'The', 'A', (4675,)), ('yous', 'you', 'A', (1701, 1712)),
    ('caslte', 'castle', 'A', (6146,)), ('frm', 'from', 'A', (5894,)),
    ('kow', 'know', 'A', (4648,)), ('relly', 'really', 'A', (6892,)),
    ("I'l", "I'll", 'A', (658,)), ('yown', 'town', 'A', (3471,)),
    ('wher', 'where', 'A', (1821,)), ('Riedock', 'Reidock', 'A', (2679, 3528)),
    ("did't", "didn't", 'A', (1202,)), ('Eveyone', 'Everyone', 'A', (6812,)),
    ('beatiful', 'beautiful', 'A', (3578,)),
    ('jounrey', 'journey', 'A', (1440,)), ('stroy', 'story', 'A', (2892,)),
    ('stange', 'strange', 'A', (3596, 4928)),
    ('daugher', 'daughter', 'A', (3123,)), ('probaly', 'probably', 'A', (339,)),
    ('stength', 'strength', 'A', (1779,)), ('Stength', 'Strength', 'A', (31,)),
    ('tring', 'trying', 'A', (4324,)),
    ('aquired', 'acquired', 'A', (155, 6076)),
    ('Mahamen', 'Mahamed', 'A', (296,)), ('bazzar', 'bazaar', 'A', (2986,)),
    ('botton', 'bottom', 'A', (5304,)),
    ('somwhere', 'somewhere', 'A', (1549,)),
    ('splendind', 'splendid', 'A', (4202,)),
    ('Baptimsal', 'Baptismal', 'A', (5098, 5099)),
    ('basptism', 'baptism', 'A', (1389,)),
    ('Congradulations', 'Congratulations', 'A', (2278,)),
    ('choise', 'choice', 'A', (2820,)), ('Unfiorms', 'Uniforms', 'A', (874,)),
    ('Tommorow', 'Tomorrow', 'A', (966,)),
    ('enegergetic', 'energetic', 'A', (2663,)),
    ('suprise', 'surprise', 'A', (554,)),
    ('Poseiden', 'Poseidon', 'A', (4583,)),
    ('forunate', 'fortunate', 'A', (191,)),
    ('incantaion', 'incantation', 'A', (4950,)),
    ('Excellect', 'Excellent', 'A', (6930,)),
    ('amoung', 'among', 'A', (4462,)), ('abscense', 'absence', 'A', (4664,)),
    ('decendant', 'descendant', 'A', (374,)),
    ('existance', 'existence', 'A', (6761,)),
    ('embarrasing', 'embarrassing', 'A', (1228,)),
    ('wimpering', 'whimpering', 'A', (64, 829)),
    ('Theather', 'Theatre', 'A', (409,)),
    ('adpot', 'adopt', 'B', (3152,)), ('convient', 'convenient', 'B', (380,)),
    ('inconvient', 'inconvenient', 'B', (1606,)),
    ('devestation', 'devastation', 'B', (1493,)),
    ('disiplined', 'disciplined', 'B', (5070,)),
    ('embarassed', 'embarrassed', 'B', (5132,)),
    ('Foribidden', 'Forbidden', 'B', (2543,)),
    ('hesistate', 'hesitate', 'B', (4176,)),
    ('occured', 'occurred', 'B', (1044,)),
    ('penninsula', 'peninsula', 'B', (239, 248)),
    ('persistant', 'persistent', 'B', (1258,)),
    ('porportional', 'proportional', 'B', (361,)),
    ('refering', 'referring', 'B', (296, 1973)),
    ('siezed', 'seized', 'B', (1003,)), ('thiefs', 'thieves', 'B', (3651,)),
    ('alot', 'a lot', 'B', (1093, 3480, 3851, 4719, 6551)),
    ('in in', 'in', 'B', (393,)), ('the the', 'the', 'B', (1888,)),
)
TYPOS_NT = ((0x0328, 'Amatuer', 'Amateur'),
            (0x0354, 'Congradulations', 'Congratulations'),
            (0x0355, 'recieved', 'received'))

# Event-flag strings the game never draws. Corrected for consistency, counted
# apart, and named here so the player-facing figure stays checkable by playing.
TYPOS_INTERNAL = (6076, 6146)

# The dictionary expander at $C3:FB23: its CMP #imm gives the lowest code and
# its LDA long gives the table. Both are read, neither is assumed.
DICT_CMP = 0x03FB25
DICT_PTR = 0x03FB30
NT_BREAK_LO, NT_BREAK_HI = 0x90, 0x9D


class Fail(Exception):
    pass


class Rom(object):
    def __init__(self, path):
        self.path = path
        self.d = io.open(path, 'rb').read()
        if len(self.d) < NT_END:
            raise Fail('%s is too small to be a DQ6 ROM (%d bytes).'
                       % (os.path.basename(path), len(self.d)))
        if self.d[ROOT_AT - 1] != 0xA2:
            raise Fail('no LDX #imm at $C0:2BFA in %s.\n  This does not look '
                       'like a DQ6 ROM.' % os.path.basename(path))
        self.root = self.d[ROOT_AT] | (self.d[ROOT_AT + 1] << 8)

    def crc(self):
        return zlib.crc32(self.d) & 0xFFFFFFFF

    def sha1(self):
        import hashlib
        return hashlib.sha1(self.d).hexdigest()

    def messages(self):
        d, out = self.d, []
        for g in range(GROUPS):
            o = TABLE + g * 3
            e = d[o] | (d[o + 1] << 8) | (d[o + 2] << 16)
            bit = (e >> 3) * 8 + (7 - (e & 7))
            for _ in range(PER_GROUP):
                syms = []
                while True:
                    node = self.root
                    while True:
                        b = (d[PAYLOAD + (bit >> 3)] >> (7 - (bit & 7))) & 1
                        bit += 1
                        base = TREE1 if b else TREE0
                        v = d[base + node] | (d[base + node + 1] << 8)
                        if v & 0x8000:
                            node = v & 0x7FFF
                        else:
                            break
                    if v in TERMINATORS:
                        break
                    syms.append(v)
                out.append((tuple(syms), v))
        return out

    def digits(self):
        """symbol -> digit character, from the ROM's own byte table."""
        out = {}
        for i in range(10):
            o = BYTETBL + (0x02 + i) * 2
            out[self.d[o] | (self.d[o + 1] << 8)] = chr(48 + i)
        return out

    def sym_of(self, b):
        o = BYTETBL + b * 2
        return self.d[o] | (self.d[o + 1] << 8)

    def letters(self):
        """character -> symbol, for the alphabet, the space and the apostrophe.

        Only the ranges the name-entry screen fixes are used, so nothing here
        depends on a glyph map. That matters: the corrections are letters, and
        a symbol whose drawn glyph is unsettled must not enter this check.
        """
        out = {}
        for i, c in enumerate('0123456789'):
            out.setdefault(c, self.sym_of(0x02 + i))
        for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
            out.setdefault(c, self.sym_of(0x10 + i))
        for i, c in enumerate('abcdefghijklmnopqrstuvwxyz'):
            out.setdefault(c, self.sym_of(0x42 + i))
        out[' '] = 0x200
        out["'"] = self.sym_of(0x77)
        return out

    def words(self, msgs):
        """Every message as a lower-case letter string, other symbols as '\\n'.

        Word boundaries are what this is for, so anything that is not a letter,
        a digit, a space or an apostrophe becomes a boundary rather than being
        named.
        """
        back = dict((s, c) for c, s in self.letters().items())
        out = []
        for syms, _t in msgs:
            out.append(''.join(back.get(s, '\n') for s in syms).lower())
        return out

    def dictionary(self):
        """name-table code -> the two charset bytes it expands to."""
        first = self.d[DICT_CMP] | self.d[DICT_CMP + 1] << 8
        base = (self.d[DICT_PTR] | self.d[DICT_PTR + 1] << 8
                | (self.d[DICT_PTR + 2] & 0x3F) << 16)
        if not 0xC0 <= first <= 0xFF:
            raise Fail('the dictionary expander at 0x%06X is not what this '
                       'check expects.' % DICT_CMP)
        out, i = {}, 0
        while self.d[base + i * 2] != 0xFF and i <= 64:
            out[first + i] = (self.d[base + i * 2], self.d[base + i * 2 + 1])
            i += 1
        return out

    def nt_tokens(self, raw):
        """A name-table entry as letters, with every other byte as <NN>.

        Dictionary codes are expanded first, so an entry re-encoded with
        different ligature choices still compares equal. Non-letter bytes are
        NOT named, for the same reason as words() above.
        """
        glyph = {}
        for i, c in enumerate('0123456789'):
            glyph.setdefault(0x02 + i, c)
        for i, c in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
            glyph.setdefault(0x10 + i, c)
        for i, c in enumerate('abcdefghijklmnopqrstuvwxyz'):
            glyph.setdefault(0x42 + i, c)
        glyph[0x01] = ' '
        glyph[0x77] = "'"
        dic = self.dictionary()
        flat = []
        for b in raw:
            flat.extend(dic[b] if b in dic else [b])
        return ''.join(glyph[b] if b in glyph else '<%02X>' % b for b in flat)

    def names(self):
        """string ID -> raw entry bytes, resolved the way $C0:315E does."""
        entries, start = [], NT_BASE
        for i in range(NT_BASE, NT_END):
            if self.d[i] == NT_TERM:
                entries.append(self.d[start:i])
                start = i + 1
        index_at, addr = {}, NT_BASE
        for n, e in enumerate(entries):
            index_at[addr] = n
            addr += len(e) + 1
        out = {}
        for g in range(NT_GROUPS):
            o = NT_PTR + g * 3
            raw = self.d[o] | self.d[o + 1] << 8 | self.d[o + 2] << 16
            a = (0xFB8703 + raw) & 0xFFFFFF
            key = ((a >> 16) & 0x3F) << 16 | (a & 0xFFFF)
            if key not in index_at:
                raise Fail('%s: name-table group %d does not line up with the '
                           'strings.' % (os.path.basename(self.path), g))
            base = index_at[key]
            for low in range(16):
                out[g * 16 + low] = entries[base + low]
        return out


def line(ok, text, detail=''):
    print('  [%s] %s%s' % ('PASS' if ok else 'FAIL', text,
                           ('   %s' % detail) if detail else ''))
    return 0 if ok else 1


def main(argv):
    if not argv or argv[0] in ('-h', '--help') or len(argv) != 2:
        print(__doc__.strip())
        return 0 if argv and argv[0] in ('-h', '--help') else 2

    base, built = Rom(argv[0]), Rom(argv[1])
    print('build verification')
    print('=' * 78)
    print('  source   %s' % os.path.basename(base.path))
    print('           %13s bytes   CRC32 %08X'
          % ('{:,}'.format(len(base.d)), base.crc()))
    print('  built    %s' % os.path.basename(built.path))
    print('           %13s bytes   CRC32 %08X'
          % ('{:,}'.format(len(built.d)), built.crc()))
    print('           SHA-1 %s' % built.sha1())
    print()

    if base.crc() == built.crc():
        raise Fail('those are the same ROM. Give the stock one first and the '
                   'patched one second.')

    bad = 0

    # 1 and 2 --------------------------------------------------------------
    old, new = base.messages(), built.messages()
    if len(old) != len(new):
        raise Fail('the two ROMs decode to different message counts.')
    dig = base.digits()

    def shows_own_id(msgs, i):
        text = ''.join(dig.get(s, '\x00') for s in msgs[i][0] if s >= GLYPH)
        return text.lstrip('\x00').startswith(str(i)) and i >= 10

    was_placeholder = set(i for i in range(len(old)) if shows_own_id(old, i))
    changed = set(i for i in range(len(old)) if old[i] != new[i])
    theirs = [i for i in range(len(old)) if i not in was_placeholder]
    touched = [i for i in theirs if old[i] != new[i]]

    # Their messages may differ in exactly two ways and no other: the redundant
    # marker $0559 removed, and a listed misspelling corrected. The marker has
    # no English glyph and in every position the engine has already drawn the
    # real mark. Anything else is their wording changed.
    letters = base.letters()
    word = set(letters[c] for c in
               'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz')
    word.add(letters["'"])

    def corrected(syms, mid):
        """Their symbols with every correction listed for this message made."""
        out = list(syms)
        for was, now, _tier, ids in TYPOS:
            if mid not in ids:
                continue
            b = [letters[c] for c in was]
            g = [letters[c] for c in now]
            at = [k for k in range(len(out) - len(b) + 1)
                  if out[k:k + len(b)] == b
                  and (k == 0 or out[k - 1] not in word)
                  and (k + len(b) == len(out) or out[k + len(b)] not in word)]
            if len(at) != 1:
                return None
            out = out[:at[0]] + g + out[at[0] + len(b):]
        return out

    listed = set(m for _w, _n, _t, ids in TYPOS for m in ids)
    marker, spelling, reworded = [], [], []
    for i in touched:
        o, n = old[i][0], new[i][0]
        want = corrected([s for s in o if s != MARKER], i)
        if want is not None and tuple(want) == n:
            (spelling if i in listed else marker).append(i)
        else:
            reworded.append(i)
    bad += line(not reworded,
                'their wording is unchanged in all %d of their messages'
                % len(theirs),
                'reworded: %d' % len(reworded))
    sites = sum(len(ids) for _w, _n, _t, ids in TYPOS)
    facing = sum(1 for _w, _n, _t, ids in TYPOS
                 for m in ids if m not in TYPOS_INTERNAL)
    ok = sorted(spelling) == sorted(listed)
    bad += line(ok,
                'their spelling corrected at the %d listed sites, and nowhere '
                'else' % sites,
                ('%d messages, %d player-facing sites, %d internal'
                 % (len(listed), facing, sites - facing)) if ok else
                ('%d of %d listed messages corrected; missing %s; unlisted %s'
                 % (len(spelling), len(listed),
                    sorted(listed - set(spelling))[:8] or 'none',
                    sorted(set(spelling) - listed)[:8] or 'none')))
    bad += line(True,
                'the redundant marker removed, and nothing else',
                '%d of their messages, symbol $%04X' % (len(marker), MARKER))
    left = sum(1 for m in new for s in m[0] if s == MARKER)
    bad += line(left == 0,
                'the marker is gone from the whole payload',
                'occurrences remaining: %d' % left)
    still = [i for i in range(len(new)) if shows_own_id(new, i)]
    bad += line(not still,
                'no message still displays its own ID',
                'remaining: %d' % len(still))
    bad += line(changed >= was_placeholder,
                'all %d unwritten messages were written'
                % len(was_placeholder),
                'left alone: %d' % len(was_placeholder - changed))
    terms = [i for i in range(len(old)) if old[i][1] != new[i][1]]
    bad += line(not terms, 'every message terminator preserved',
                'differing: %d' % len(terms))
    print()

    # The attestation rule, measured rather than asserted. Clause A of the
    # spelling rule says the ROM itself attests the corrected form somewhere in
    # their own writing. This resolves every tier-A target in the STOCK ROM and
    # fails if one of them is not there, which is what stops the rule from
    # quietly widening into "whatever looks right to me".
    stock_text = '\n'.join(base.words(old))
    missing, found = [], {}
    for was, now, tier, _ids in TYPOS:
        if tier != 'A':
            continue
        n = len(re.findall(r"(?<![a-z0-9'])" + re.escape(now.lower())
                           + r"(?![a-z0-9'])", stock_text))
        found[now] = n
        if n == 0:
            missing.append('%s -> %s' % (was, now))
    tier_a = sum(1 for _w, _n, t, _i in TYPOS if t == 'A')
    tier_b = sum(1 for _w, _n, t, _i in TYPOS if t == 'B')
    bad += line(not missing,
                'every tier-A correction is attested in their own text',
                '%d of %d checked, %d unattested%s'
                % (tier_a, tier_a + tier_b, len(missing),
                   (': ' + ', '.join(missing)) if missing else ''))
    if found:
        least = min(found, key=lambda k: found[k])
        print('       thinnest attestation: %r appears %d time%s in the stock '
              'ROM' % (least, found[least], '' if found[least] == 1 else 's'))
        print('       (tier B is %d corrections that are not English words and '
              'have one' % tier_b)
        print('       English spelling each, so there is nothing of theirs to '
              'attest)')
    print()

    # 3 --------------------------------------------------------------------
    on, nn = base.names(), built.names()
    ids = sorted(on)
    diff = [i for i in ids if on[i] != nn[i]]
    same = len(ids) - len(diff)
    bad += line(True, 'name table resolved by string ID in both ROMs',
                '%d IDs' % len(ids))
    print('       %d changed, %d untouched' % (len(diff), same))
    print('       (the table is repacked wholesale, so this is the only')
    print('       comparison that means anything. A byte diff would show')
    print('       almost the whole region as different and prove nothing.)')
    print()

    # The animal counter is deliberately EMPTY, following the translation's own
    # convention for a string English does not express: 75 of their entries are
    # blank where the Japanese has content. It is asserted here because a blank
    # cannot be eyeballed in a diff and because the row that produces it is a
    # sentinel in nametable-en.txt - if that sentinel ever stops being
    # recognised the entry silently reverts to displaying its identifier.
    bad += line(nn[COUNTER_ID] == b'',      # names() yields raw bytes
                'the animal counter is blank, not an identifier',
                '$%04X' % COUNTER_ID)

    # The three misspellings in their name table. Compared as letters with
    # every other byte left as <NN>, so a re-encoding that picks different
    # ligatures still compares equal and no claim is made about any glyph.
    nt_bad = []
    for sid, was, now in TYPOS_NT:
        before, after = base.nt_tokens(on[sid]), built.nt_tokens(nn[sid])
        if was not in before or after != before.replace(was, now, 1):
            nt_bad.append('$%04X %r -> %r' % (sid, before, after))
    bad += line(not nt_bad,
                'the %d misspellings in their name table are corrected, and '
                'the entries are otherwise identical' % len(TYPOS_NT),
                '; '.join(nt_bad) if nt_bad else
                ', '.join('$%04X' % s for s, _w, _n in TYPOS_NT))
    print()

    # 4 --------------------------------------------------------------------
    span = built.d[CF_SPAN:CF_SPAN + len(CF_AFTER)] == CF_AFTER
    bad += line(span, 'Info > All: the 87-byte span is restored',
                '0x%06X' % CF_SPAN)
    sites = sum(1 for off, want in CF_RELOCATIONS
                if (built.d[off + 1] | built.d[off + 2] << 8) == want)
    branches = sum(1 for off, want in CF_BRANCHES if built.d[off] == want)
    bad += line(sites == len(CF_RELOCATIONS) and branches == len(CF_BRANCHES),
                'Forget: word-wrap state relocated',
                '%d/%d operands, %d/%d branches'
                % (sites, len(CF_RELOCATIONS), branches, len(CF_BRANCHES)))
    print()

    # 5 --------------------------------------------------------------------
    code = built.d[GOLD_CODE_AT:GOLD_CODE_AT + len(GOLD_CODE_NOW)]
    bad += line(code == GOLD_CODE_NOW, 'gold window: the draw call is back',
                '0x%06X' % GOLD_CODE_AT)
    desc = built.d[GOLD_DESC_AT:GOLD_DESC_AT + len(GOLD_DESC_NOW)]
    bad += line(desc == GOLD_DESC_NOW, 'gold window: descriptor 58 moved',
                'x=%d y=%d w=%d' % tuple(desc))
    win_lo, win_hi = 0x057B5C, 0x057B5C + 14 * 128
    moved = [i for i in range(win_lo, win_hi)
             if base.d[i] != built.d[i] and not
             GOLD_DESC_AT <= i < GOLD_DESC_AT + 14]
    bad += line(not moved, 'no other window descriptor changed',
                '%d bytes differ elsewhere in the table' % len(moved))
    print()

    # 6 --------------------------------------------------------------------
    bad += line(base.d[HDR + 0x15:HDR + 0x18] == built.d[HDR + 0x15:HDR + 0x18],
                'header mapmode and ROM size unchanged')
    ck = int.from_bytes(built.d[HDR + 0x1E:HDR + 0x20], 'little')
    cx = int.from_bytes(built.d[HDR + 0x1C:HDR + 0x1E], 'little')
    total = sum(built.d) & 0xFFFF
    bad += line((ck ^ cx) == 0xFFFF and ck == total,
                'internal checksum consistent',
                '%04X, complement %04X, recomputed %04X' % (ck, cx, total))
    print()

    if bad:
        print('  %d check%s failed.' % (bad, '' if bad == 1 else 's'))
        print()
        return 1
    print('  Everything checked here passes. That is not the same as')
    print('  "the game is correct": these are structural checks, and text')
    print('  that is correctly inserted can still read badly or overrun a')
    print('  window. Play it.')
    print()
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except Fail as exc:
        print('\nERROR: %s\n' % exc, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError as exc:
        print('\nERROR: cannot open %s\n' % exc.filename, file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)
