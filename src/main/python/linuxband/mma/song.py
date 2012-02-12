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

import cStringIO
import logging
from linuxband.mma.parse import parse
from linuxband.mma.song_data import SongData
from linuxband.mma.bar_info import BarInfo

class Song(object):

    def __init__(self, midi_generator):
        self.__clear_song()
        self.__midi_generator = midi_generator

    def get_data(self):
        return self.__song_data

    def load_from_file(self, file_name):
        logging.info("Loading file '%s'", file_name)
        try:
            mma_file = file(file_name, 'r')
            try:
                mma_data = mma_file.read()
            finally:
                mma_file.close()
        except:
            logging.exception("Unable to open '" + file_name + "' for input")
            return -2
        self.__pending_mma_data = mma_data
        self.__song_data.set_save_needed(False)

    def load_from_string(self, mma_data):
        self.__pending_mma_data = mma_data
        self.__song_data.set_save_needed(True)

    def compile_song(self):
        if not self.__song_data.is_save_needed() and self.__pending_mma_data == None and self.__invalid_mma_data == None:
            logging.debug('No compilation needed')
            return self.__last_compile_result
        if self.__pending_mma_data == None:
            mma_data = self.write_to_string()
            res = self.__midi_generator.check_mma_syntax(mma_data)
        else:
            res = self.__do_compile(self.__pending_mma_data)
            self.__pending_mma_data = None
        return res

    def write_to_mma_file(self, file_name):
        mma_data = self.write_to_string()
        self.__do_write_to_file(file_name, mma_data)
        self.__song_data.set_save_needed(False)

    def write_to_midi_file(self, file_name):
        mma_data = self.write_to_string()
        res, midi = self.__midi_generator.generate_smf(mma_data)
        if res == 0: self.__do_write_to_file(file_name, midi)

    def write_to_string(self):
        """ 
        If the mma was parsed correctly return it. Otherwise give the invalid mma data back.
        """
        if self.__invalid_mma_data == None:
            return self.__song_data.write_to_string()
        else:
            return self.__invalid_mma_data

    def get_playback_midi_data(self):
        """ 
        Get midi file which will be sent to the client.
        
        Than create mma file with markers for tracking and generate the resulting midi from it.
        """
        mma_data_marks = self.__song_data.write_to_string_with_midi_marks()
        return self.__midi_generator.generate_smf(mma_data_marks)

    def __clear_song(self):
        """
        Called when parsing of mma data failed.
        
        E.g. during opening the new file or parsing data from the source editor.
        The song must have minimum one BarInfo on which the cursor is located.
        
        bar_count = number of bar_chords in the song, number of bar_info is bar_count + 1
        """
        self.__song_data = SongData([ BarInfo() ], [], 0)
        self.__invalid_mma_data = None
        self.__pending_mma_data = None
        self.__last_compile_result = None

    def __do_compile(self, mma_data):
        res = self.__last_compile_result = self.__midi_generator.check_mma_syntax(mma_data)
        if res == 0:
            mma_file = cStringIO.StringIO(mma_data)
            try:
                self.__song_data = parse(mma_file)
            except ValueError:
                logging.exception("Failed to parse the file.")
                res = -1
            mma_file.close()
        if res > 0 or res == -1:
            self.__clear_song()
            self.__invalid_mma_data = mma_data
            self.__song_data.set_save_needed(True)
        else:
            self.__invalid_mma_data = None
        return res

    def __do_write_to_file(self, file_name, data):
        logging.info('Opening output file %s', file_name)
        try:
            f = file(file_name, 'w')
            try:
                f.write(data)
            finally:
                f.close()
        except:
            logging.exception("Failed to save data to '" + file_name + "'.")
