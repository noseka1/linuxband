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

import copy
import logging


class BarChords:

    def __init__(self):
        self.__song_data = None
        self.__before_number = ''
        self.__number = None
        self.__after_number = ' '
        self.__chords = [[ '/', '' ]] # one chord is always there
        self.__eol = '\n'

    def set_song_data(self, song_data):
        self.__song_data = song_data

    def set_before_number(self, before_number):
        self.__before_number = before_number

    def get_before_number(self):
        return self.__before_number

    def get_number(self):
        return self.__number

    def set_number(self, number):
        self.__number = number

    def set_after_number(self, after_number):
        self.__after_number = after_number

    def get_after_number(self):
        return self.__after_number

    def set_chords(self, chords):
        self.__chords = chords

    def get_chords(self):
        return self.__chords

    def set_eol(self, eol):
        self.__eol = eol

    def get_eol(self):
        return self.__eol

    def set_chord(self, beat_num, chord):
        """ 
        Save one chord on given beat.
        
        If chord == '' then actually delete the chord.
        """
        # [['Dm', ' '], ['/', ' '], ['AmzC@3.2', ' '], ['z!', '\n']]
        chords = self.__chords
        song_data = self.__song_data
        if chord == '' and beat_num >= len(self.__chords):
            return
        if beat_num + 1 < len(chords): # there's a chord after this beat
            full_chord = chords[beat_num]
            if not chord: chord = '/'
            if full_chord[0] != chord:
                full_chord[0] = chord
                song_data.changed()
        else:
            if not chord: # delete a chord
                full_chord = chords[beat_num]
                if beat_num > 0: # there is some chord before us
                    # possibly move trailing string from our chord to eol
                    self.__eol = ''.join(full_chord[1:]) + self.__eol
                    chords.pop(beat_num)
                    song_data.changed()
                else: # the only chord on the line
                    if full_chord[0] != '/':
                        full_chord[0] = '/'
                        song_data.changed()
            else: # add or replace chord
                if beat_num < len(chords): # replace an existing chord
                    full_chord = chords[beat_num]
                    if full_chord[0] != chord:
                        full_chord[0] = chord
                        song_data.changed()
                else: # append a chord
                    last_full_chord = chords[len(chords) - 1]
                    if len(last_full_chord[1]) == len(last_full_chord[1].rstrip()):
                        last_full_chord[1] = last_full_chord[1] + ' '
                    while len(chords) < beat_num: chords.append(['/', ' '])
                    chords.append([chord, ''])
                    song_data.changed()

    def get_as_string_list(self):
        res = []
        res.append(self.__before_number)
        if self.get_number() != None:
            res.append(str(self.get_number()))
        res.append(self.__after_number)
        for full_chord in self.__chords:
            res.extend(full_chord)
        res.append(self.__eol)
        return res

    def show_debug(self):
        logging.debug("Num: '%s'" % self.__number)
        logging.debug("AfterNum: '%s'" % self.__after_number)
        logging.debug("Chords: '%s'" % self.__chords)
        logging.debug("Eol: '%s'" % self.__eol)

    def __deepcopy__(self, memo):
        newone = BarChords()
        newone.__song_data = self.__song_data
        newone.__number = self.__number
        newone.__after_number = copy.deepcopy(self.__after_number, memo)
        newone.__chords = copy.deepcopy(self.__chords, memo)
        newone.__eol = copy.deepcopy(self.__eol, memo)
        return newone
