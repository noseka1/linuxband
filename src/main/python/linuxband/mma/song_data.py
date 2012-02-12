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
from linuxband.mma.bar_info import BarInfo
from linuxband.mma.bar_chords import BarChords
from linuxband.glob import Glob

class SongData(object):

    # how many additional lines are needed for one bar in the mma file
    # used for line tracking when playing midi
    __LINES_PER_BAR = 5
    __LINES_ADD = 1

    def __init__(self, bar_info, bar_chords, bar_count):
        self.__bar_info = bar_info
        self.__bar_chords = bar_chords
        self.__bar_count = bar_count
        self.__beats_per_bar = 4 # TODO Beats/bar, set with TIME        
        self.__save_needed = False
        for bar_info in self.__bar_info:
            bar_info.set_song_data(self)
        for bar_chord in self.__bar_chords:
            bar_chord.set_song_data(self)

    def get_bar_info_all(self):
        return self.__bar_info

    def get_bar_count(self):
        return self.__bar_count

    def get_beats_per_bar(self):
        return self.__beats_per_bar

    def set_bar_info(self, bar_num, bar_info):
        self.__bar_info[bar_num] = copy.deepcopy(bar_info)
        self.__save_needed = True

    def get_bar_info(self, bar_num):
        return self.__bar_info[bar_num]

    def set_bar_chords(self, bar_num, bar_chords):
        """ Replaces chords in the bar and fixes the bar number. """
        bar_chords = self.__bar_chords[bar_num] = copy.deepcopy(bar_chords)
        if bar_num > 0:
            prev = self.__bar_chords[bar_num - 1].get_number()
            if prev:
                bar_chords.set_number(prev + 1)
        self.__save_needed = True

    def get_bar_chords(self, bar_num):
        return self.__bar_chords[bar_num]

    def set_save_needed(self, save_needed):
        self.__save_needed = save_needed

    def is_save_needed(self):
        return self.__save_needed

    def changed(self):
        logging.debug('Song changed');
        self.__save_needed = True

    def create_bar_info(self):
        bar_info = BarInfo()
        bar_info.set_song_data(self)
        return bar_info

    def create_bar_chords(self):
        bar_chords = BarChords()
        bar_chords.set_song_data(self)
        return bar_chords

    def change_bar_count(self, new_bar_count):
        bar_info = self.__bar_info
        bar_chords = self.__bar_chords
        bar_count = self.__bar_count
        if new_bar_count > bar_count:
            i = 0
            diff = new_bar_count - bar_count
            while i < diff:
                # append None and then call set_bar_chords method which computes the bar number
                bar_chords.append(None)
                self.set_bar_chords(len(bar_chords) - 1, self.create_bar_chords())
                bar_info.append(self.create_bar_info())
                self.__bar_count += 1
                i = i + 1
        elif new_bar_count < bar_count:
            i = 0
            diff = bar_count - new_bar_count
            while i < diff:
                bar_chords.pop()
                bar_info.pop()
                self.__bar_count -= 1
                i = i + 1
        self.__save_needed = True

    def get_title(self):
        lines = self.__bar_info[0].get_lines()
        if len(lines) > 0:
            if lines[0][0] == Glob.A_REMARK:
                comm = lines[0][-1].strip()
                comm = comm [2:] # remove '//'
                return comm.strip()
        return Glob.UNTITLED_SONG_NAME

    def set_title(self, title):
        bar_info = self.__bar_info[0]
        # get first line
        lines = bar_info.get_lines()
        if len(lines) == 0 or lines[0][0] <> Glob.A_REMARK:
            line = [Glob.A_REMARK, ""]
            bar_info.insert_line(line)
        else:
            line = lines[0]
        line[-1] = "// " + title + "\n"
        self.__save_needed = True

    def write_to_string(self):
        mma_array = []
        for i in range(0, self.__bar_count):
            mma_array.extend(self.__bar_info[i].get_as_string_list())
            mma_array.extend(self.__bar_chords[i].get_as_string_list())
        mma_array.extend(self.__bar_info[self.__bar_count].get_as_string_list())
        return ''.join(mma_array)

    def write_to_string_with_midi_marks(self):
        """
        Write the mma file which will be compiled by mma and played in midi player.
        
        We use macros to wrap chords. It allows the tracking of which bar is played.
        """
        mma_array = []
        # write header with macro definitions
        for i in range(0, self.__bar_count):
            mma_array.extend("MSet MacroBar%i\n" % i)
            mma_array.extend("MidiMark BAR%i\n" % i)
            mma_array.extend("MidiMark $_LineNum\n")
            mma_array.extend(self.__bar_chords[i].get_as_string_list())
            if i == self.__bar_count - 1:
                mma_array.extend("MidiMark END\n")
            mma_array.extend("MSetEnd\n") # 5 lines
        # write the song
        for i in range(0, self.__bar_count):
            mma_array.extend(self.__bar_info[i].get_as_string_list())
            mma_array.extend("$MacroBar%i\n" % i)
        mma_array.extend(self.__bar_info[self.__bar_count].get_as_string_list())
        return ''.join(mma_array)

    def write_tokens_debug(self):
        """ For debugging purposes. """
        for i in range(0, self.__bar_count):
            self.__bar_info[i].show_debug()
            self.__bar_chords[i].show_debug()
        self.__bar_info[self.__bar_count].show_debug()

    def get_mma_line_offset(self):
        return self.__bar_count * SongData.__LINES_PER_BAR + SongData.__LINES_ADD
