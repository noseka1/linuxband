# Copyright (c) 2012 Ales Nosek <ales.nosek@gmail.com>
#
# This file is part of LinuxBand.
#
# LinuxBand is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

"""
This file includes code found in MMA's 12.01 parse.py file,
written by Bob van der Poel <bob@mellowood.ca>

This module does all file parsing. Most commands
are passed to the track classes; however, things
like TIME, SEQRND, etc. which just set global flags
are completely handled here.

"""

from linuxband.glob import Glob
from linuxband.mma.bar_chords import BarChords
from linuxband.mma.bar_info import BarInfo
from linuxband.mma.song_data import SongData

########################################
# File processing. Mostly jumps to pats
########################################

def parse(inpath):
    """
    Process a mma input file.
    """
    song_bar_info = []
    song_bar_chords = []
    song_bar_count = 0
    bar_number = 0
    bar_info = BarInfo()
    bar_chords = BarChords()

    while True:
        curline = inpath.readline()

        # EOF
        if not curline:
            song_bar_info.append(bar_info) # song_bar_info has always one element more then song_bar_chords
            song_bar_count = bar_number
            return SongData(song_bar_info, song_bar_chords, song_bar_count)

        """ convert 0xa0 (non-breakable space) to 0x20 (regular space).
        """
        curline = curline.replace('\xa0', '\x20')

        # empty line
        if curline.rstrip('\n').strip() == '':
            bar_info.add_line([Glob.A_UNKNOWN, curline]);
            continue

        l = curline.split()

        # line beginning with macro
        if l[0][0] == '$':
            wline = get_wrapped_line(inpath, curline)
            wline.insert(0, Glob.A_UNKNOWN)
            bar_info.add_line(wline)
            continue


        """ Handle BEGIN and END here. This is outside of the Repeat/End
            and variable expand loops so SHOULD be pretty bullet proof.
            Note that the beginData stuff is global to this module ... the
            Include/Use directives check to make sure we're not doing that
            inside a Begin/End.

            beginData[] is a list which we append to as more Begins are
            encountered.

            The placement here is pretty deliberate. Variable expand comes
            later so you can't macroize BEGIN ... I think this makes sense.

            The tests for 'begin', 'end' and the appending of the current
            begin[] stuff have to be here, in this order.
        """

        action = l[0].upper()      # 1st arg in line

        # parse BEGIN and END block
        if action == 'BEGIN':
            block_action = l[1].upper()
            begin_block = parse_begin_block(inpath, curline)
            if block_action in supported_block_actions:
                tokens = parse_supported_block_action(block_action, begin_block)
                begin_block = tokens
            begin_block.insert(0, Glob.A_BEGIN_BLOCK)
            begin_block.insert(1, block_action)
            bar_info.add_line(begin_block)
            continue

        # parse MSET block
        if action == 'MSET':
            mset_block = parse_mset_block(inpath, curline)
            mset_block.insert(0, Glob.A_UNKNOWN)
            bar_info.add_line(mset_block)
            continue

        # parse IF - ENDIF block
        if action == 'IF':
            if_block = parse_if_block(inpath, curline)
            if_block.insert(0, Glob.A_UNKNOWN)
            bar_info.add_line(if_block)
            continue

        # supported commands
        if action in supported_actions:
            wline = get_wrapped_line_join(inpath, curline)
            tokens = parse_supported_action(action, wline)
            tokens.insert(0, action)
            bar_info.add_line(tokens)
            continue

        # if the command is in the simple function table
        if action in simple_funcs:
            wline = get_wrapped_line(inpath, curline)
            wline.insert(0, Glob.A_UNKNOWN)
            bar_info.add_line(wline)
            continue

        """ We have several possibilities ...
            1. The command is a valid assigned track name,
            2. The command is a valid track name, but needs to be
               dynamically allocated,
            3. It's really a chord action
        """

        # track function BASS/DRUM/APEGGIO/CHORD ...
        if '-' in action:
            trk_class, ext = action.split('-', 1) #@UnusedVariable
        else:
            trk_class = action

        if trk_class in trk_classes:
            # parsing track sequence ?
            parse_seq = len(l) >= 1 and l[1].upper() == 'SEQUENCE'
            wline = []
            while True:
                wline.extend(get_wrapped_line(inpath, curline))
                if not parse_seq: break
                """ Count the number of { and } and if they don't match read more lines and 
                    append. If we get to the EOF then we're screwed and we error out. """
                wline2 = ''.join(wline)
                if wline2.count('{') == wline2.count('}'): break
                curline = inpath.readline()
                if not curline:
                    raise ValueError("Reached EOF, Sequence {}s do not match")
            wline.insert(0, Glob.A_UNKNOWN)
            bar_info.add_line(wline)
            continue

        # join the wrapped line into one line
        wline = get_wrapped_line_join(inpath, curline)

        if wline[0].replace('\\\n', '').strip() == '':
            # line is a comment or empty wrapped line
            act = Glob.A_REMARK if wline[1].strip() else Glob.A_UNKNOWN
            bar_info.add_line([act , wline[0], wline[1]])
            continue

        l, eol = wline
        ### Gotta be a chord data line!

        """ A data line can have an optional bar number at the start
            of the line. Makes debugging input easier. The next
            block strips leading integers off the line. Note that
            a line number on a line by itself it okay.
        """

        before_number = ''
        if action.isdigit():   # isdigit() matches '1', '1234' but not '1a'!
            l2 = l.lstrip()
            before_number_len = len(l) - len(l2)
            before_number = l[0:before_number_len]
            l = l2
            numstr = l.split()[0]
            bar_chords.set_number(int(numstr))
            l = l[len(numstr):] # remove number
            if len(l.strip()) == 0: # ignore empty lines
                bar_info.add_line([ Glob.A_UNKNOWN, wline[0] + wline[1] ])
                continue

        """ We now have a valid line. It'll look something like:

            'Cm', '/', 'z', 'F#@4.5' { lyrics } [ solo ] * 2 
            

            Special processing in needed for 'z' options in chords. A 'z' can
            be of the form 'CHORDzX', 'z!' or just 'z'.
        """
        after_number = None
        last_chord = []
        ctable = []
        i = 0
        solo_count = 0
        lyrics_count = 0
        mismatched_solo = "Mismatched {}s for solo found in chord line"
        mismatched_lyrics = "Mismatched []s for lyrics found in chord line"
        while True:
            chars = ''
            while i < len(l):
                ch = l[i]
                if ch == '{':
                    """ Extract solo(s) from line ... this is anything in {}s.
                        The solo data is pushed into RIFFs and discarded from
                        the current line.
                    """
                    solo_count += 1
                elif ch == '[':
                    """ Set lyrics from [stuff] in the current line.
                        NOTE: lyric.extract() inserts previously created
                        data from LYRICS SET and inserts the chord names
                        if that flag is active.
        
                    """
                    lyrics_count += 1
                elif ch == '}':
                    solo_count -= 1
                    if solo_count < 0:
                        raise ValueError(mismatched_solo)
                elif ch == ']':
                    lyrics_count -= 1
                    if lyrics_count < 0:
                        raise ValueError(mismatched_lyrics)
                elif ch == '*':
                    """ A bar can have an optional repeat count. This must
                        be at the end of bar in the form '* xx'.
                    """
                    pass
                elif ch in '\t\n\\ 0123456789': # white spaces, \ and repeat count
                    pass
                elif solo_count == 0 and lyrics_count == 0: # found beginning of the chord
                    break
                chars += ch
                i += 1
            if i == len(l): # no more chord is coming
                if solo_count != 0:
                    raise ValueError(mismatched_solo)
                if lyrics_count != 0:
                    raise ValueError(mismatched_lyrics)
                if after_number == None:
                    after_number = chars
                else:
                    last_chord.append(chars)
                    ctable.append(last_chord)
                break
            else: # chord beginning
                if after_number == None:
                    after_number = chars
                else:
                    last_chord.append(chars)
                    ctable.append(last_chord)
                chord_begin = i
                # find the end of the chord
                while i < len(l):
                    if l[i] in '{}[]*\t\n\\ ':
                        break
                    i += 1
                # chord examples: '/', 'z', 'Am7@2', 'Am6zC@3'
                c = l[chord_begin:i]
                last_chord = [ c ]
        # the trailing string of the last chord can possibly include '\n' after which
        # it would be difficult to add further chords. Therefore move the trailing string
        # of the last chord to eol
        eol = last_chord[1] + eol
        last_chord[1] = ''

        bar_chords.set_before_number(before_number)
        bar_chords.set_after_number(after_number)
        bar_chords.set_eol(eol)
        bar_chords.set_chords(ctable)

        song_bar_info.append(bar_info)
        song_bar_chords.append(bar_chords)

        bar_number = bar_number + 1
        bar_info = BarInfo()
        bar_chords = BarChords()


def get_wrapped_line(inpath, curline):
    """
    Reads the whole wrapped line ('\' at the end) and stores it in a list.
    
    The lines in the list are not modified and are the same as in the file
    """
    result = []
    while True:
        if not curline:
            raise ValueError("Reached EOF, the last line is not complete")
        result.append(curline)
        curline = curline.strip()
        if not curline or not(curline[-1] == '\\'):
            break
        curline = inpath.readline()
    return result


def get_wrapped_line_join(inpath, curline):
    """
    Reads the wrapped line and joins it into one.

    Returns array of two strings: 
        1) the line content which will be further parsed
        2) comment with '\n' at the end
    If you join those strings you get exactly what was stored in the file
    """
    wrapped = get_wrapped_line(inpath, curline)
    line = ''
    comment = ''
    i = 0
    while i < len(wrapped):
        l = wrapped[i]
        if comment:
            comment = comment + l
        else:
            if '//' in l:
                l, comm = l.split('//', 1)
                comment = '//' + comm
                line = line + l
            else:
                line = line + l
        i = i + 1
    return [ line, comment ]


def parse_begin_block(inpath, curline):
    beginDepth = 1
    result = [ curline ]
    while True:
        curline = inpath.readline()
        if not curline:
            raise ValueError("Reached EOF while looking for End")
        l = curline.split()
        action = None
        if len(l) > 0:
            action = l[0].upper()
        if action == 'BEGIN':
            beginDepth = beginDepth + 1
        if action == 'END':
            beginDepth = beginDepth - 1
        result.append(curline)
        if beginDepth == 0:
            break
    return result

def parse_mset_block(inpath, curline):
    l = curline.split()
    if len(l) < 2:
        raise ValueError("Use: MSET VARIABLE_NAME <lines> MsetEnd")
    result = [ curline ]
    while True:
        curline = inpath.readline()
        if not curline:
            raise ValueError("Reached EOF while looking for MSetEnd")
        l = curline.split()
        action = None
        if len(l) > 0:
            action = l[0].upper()
        result.append(curline)
        if action in ("MSETEND", 'ENDMSET'):
            break
    return result

def parse_if_block(inpath, curline):
    ifDepth = 1
    result = [ curline ]
    while True:
        curline = inpath.readline()
        if not curline:
            raise ValueError("Reached EOF while looking for EndIf")
        l = curline.split()
        action = None
        if len(l) > 0:
            action = l[0].upper()
        if action == 'IF':
            ifDepth = ifDepth + 1
        if action in ('ENDIF', 'IFEND'):
            ifDepth = ifDepth - 1
        result.append(curline)
        if ifDepth == 0:
            break
    return result

def parse_supported_action(action, wline):
    line = []
    if action == Glob.A_AUTHOR: # ['Author', ' Bob van der Poel\n']
        line = tokenize_line(wline[0], 1)
    elif action == Glob.A_DEF_GROOVE: # ['DefGroove', ' ', 'ModernJazz', '   ModernJazz with just a piano and guitar.\n']
        line = tokenize_line(wline[0], 2)
    elif action == Glob.A_GROOVE: # ['Groove', ' ', 'Tango', ' LightTango LightTangoSus LightTango\n']
        line = tokenize_line(wline[0], 2)
    elif action == Glob.A_REPEAT: # nothing to parse
        line = [ wline[0] ]
    elif action == Glob.A_REPEAT_END: # ['RepeatEnd', ' ', '2', '\n'] or ['RepeatEnd', '\n' ]
        line = tokenize_line(wline[0], 2)
    elif action == Glob.A_REPEAT_ENDING: #
        line = tokenize_line(wline[0], 2)
    elif action == Glob.A_TEMPO: # ['Tempo', ' ', '120', '\n']
        line = tokenize_line(wline[0], 2)
    elif action == Glob.A_TIME: # ['Time', ' ', '4'. '\n' ]
        line = tokenize_line(wline[0], 2)
    line.append(wline[1])
    return line

def parse_supported_block_action(block_action, begin_block):
    return [ begin_block[0], ''.join(begin_block[1:-1]), begin_block[-1] ]

def tokenize_line(line, limit):
    """
    Split the line into tokens and characters in between.
    
    Example:
    ['Time', ' ', '4', '\n']
    ['Timesig', ' ', '4', ' ', '4', '\n']
    ['DefGroove', ' ', 'ModernJazz', '    ModernJazz with just a piano and guitar.\n'] 
    """
    chars_between = '\t\n\\ '
    tokenized_line = []
    count = 0
    start = 0
    end = 0
    read_token = True
    while start < len(line):
        if read_token:
            while end < len(line) and line[end] not in chars_between:
                end += 1
            tokenized_line.append(line[start:end])
            count += 1
            if count == limit:
                tokenized_line.append(line[end:])
                break
        else:
            while end < len(line) and line[end] in chars_between:
                end += 1
            tokenized_line.append(line[start:end])
        read_token = not read_token
        start = end
    return tokenized_line

""" =================================================================

    Command jump tables. These need to be at the end of this module
    to avoid undefined name errors. The tables are only used in
    the parse() function.

    The first table is for the simple commands ... those which DO NOT
    have a leading track name. The second table is for commands which
    require a leading track name.

    The alphabetic order is NOT needed, just convenient.

"""

simple_funcs = \
    'ADJUSTVOLUME', \
    'ALLGROOVES', \
    'ALLTRACKS', \
    'AUTHOR', \
    'AUTOSOLOTRACKS', \
    'BEATADJUST', \
    'CHANNELPREF', \
    'CHORDADJUST', \
    'COMMENT', \
    'CRESC', \
    'CUT', \
    'DEBUG', \
    'DEC', \
    'DECRESC', \
    'DEFALIAS', \
    'DEFCHORD', \
    'DEFGROOVE', \
    'DELETE', \
    'DOC', \
    'DOCVAR', \
    'DRUMVOLTR', \
    'ELSE', \
    'ENDIF', \
    'ENDMSET', \
    'ENDREPEAT', \
    'EOF', \
    'FERMATA', \
    'GOTO', \
    'GROOVE', \
    'GROOVECLEAR', \
    'IF', \
    'IFEND', \
    'INC', \
    'INCLUDE', \
    'KEYSIG', \
    'LABEL', \
    'LYRIC', \
    'MIDIDEF', \
    'MIDI', \
    'MIDICOPYRIGHT' \
    'MIDICUE' \
    'MIDIFILE', \
    'MIDIINC', \
    'MIDIMARK', \
    'MIDISPLIT', \
    'MIDITEXT' \
    'MIDITNAME' \
    'MMAEND', \
    'MMASTART', \
    'MSET', \
    'MSETEND', \
    'NEWSET', \
    'PATCH', \
    'PRINT', \
    'PRINTACTIVE', \
    'PRINTCHORD', \
    'REPEAT', \
    'REPEATEND', \
    'REPEATENDING', \
    'RESTART', \
    'RNDSEED', \
    'RNDSET', \
    'SEQ', \
    'SEQCLEAR', \
    'SEQRND', \
    'SEQRNDWEIGHT', \
    'SEQSIZE', \
    'SET', \
    'SETAUTOLIBPATH', \
    'SETINCPATH', \
    'SETLIBPATH', \
    'SETMIDIPLAYER', \
    'SETOUTPATH', \
    'SETSYNCTONE', \
    'SHOWVARS', \
    'STACKVALUE', \
    'SWELL', \
    'SWINGMODE', \
    'SYNCHRONIZE', \
    'TEMPO', \
    'TIME', \
    'TIMESIG', \
    'TONETR', \
    'TRUNCATE', \
    'UNSET', \
    'USE', \
    'VARCLEAR', \
    'VEXPAND', \
    'VOICEVOLTR', \
    'VOICETR', \
    'VOLUME', \
    'TRANSPOSE'


trackFuncs = \
    'ACCENT', \
    'ARPEGGIATE' \
    'ARTICULATE' \
    'CHANNEL', \
    'DUPRIFF', \
    'MIDIVOLUME', \
    'MIDICRESC', \
    'MIDIDECRESC', \
    'CHSHARE', \
    'COMPRESS', \
    'COPY', \
    'CRESC', \
    'CUT', \
    'DECRESC', \
    'DELAY', \
    'DIRECTION', \
    'DRUMTYPE', \
    'DUPROOT', \
    'FORCEOUT', \
    'GROOVE', \
    'HARMONY', \
    'HARMONYONLY', \
    'HARMONYVOLUME', \
    'INVERT', \
    'LIMIT', \
    'MALLET', \
    'MIDICLEAR' \
    'MIDICUE' \
    'MIDIDEF', \
    'MIDIGLIS', \
    'MIDIPAN', \
    'MIDISEQ', \
    'MIDITEXT' \
    'MIDITNAME', \
    'MIDIVOICE', \
    'OCTAVE', \
    'OFF', \
    'ON', \
    'ORNAMENT' \
    'TUNING' \
    'CAPO' \
    'RANGE', \
    'RESTART', \
    'RIFF', \
    'RSKIP', \
    'RTIME', \
    'RVOLUME', \
    'SCALETYPE', \
    'SEQCLEAR', \
    'SEQRND', \
    'SEQUENCE', \
    'SEQRNDWEIGHT', \
    'SWELL', \
    'MIDINOTE' \
    'NOTESPAN', \
    'STRUM', \
    'TONE', \
    'UNIFY', \
    'VOICE', \
    'VOICING', \
    'VOLUME', \
    'DEFINE'

trk_classes = \
    'BASS', \
    'CHORD', \
    'ARPEGGIO', \
    'SCALE', \
    'DRUM', \
    'WALK', \
    'MELODY', \
    'SOLO', \
    'ARIA', \
    'PLECTRUM'

supported_actions = \
    Glob.A_AUTHOR, \
    Glob.A_DEF_GROOVE, \
    Glob.A_GROOVE, \
    Glob.A_REPEAT, \
    Glob.A_REPEAT_END, \
    Glob.A_REPEAT_ENDING, \
    Glob.A_TEMPO, \
    Glob.A_TIME

supported_block_actions = \
    Glob.A_DOC
