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

import sys
import logging
from linuxband.logger import Logger
from linuxband.mma.parse import parse


class TestParse(object):

    def test_parse(self, input_name):
        song_data = self.__load_file(input_name)
        if not song_data: return -1
        mma_out = song_data.write_to_string()
        output_name = input_name + ".out"
        try:
            fout = open(output_name, 'w')
            fout.write(mma_out)
            fout.close()
        except:
            logging.exception("Failed to save data to '" + output_name + "'.")
            return -1
        logging.info('Written file %s' % output_name)
        return 0

    def test_tokens(self, input_name):
        song_data = self.__load_file(input_name)
        if not song_data: return -1
        song_data.write_tokens_debug()
        return 0

    def test_midi_marks(self, input_name):
        song_data = self.__load_file(input_name)
        if not song_data: return -1
        logging.info('\n%s' % song_data.write_to_string_with_midi_marks())
        return 0

    def __load_file(self, input_name):
        logging.info('Parsing file %s' % input_name)
        try:
            fin = file(input_name, 'r')
            song_data = parse(fin)
            fin.close()
        except:
            logging.exception("Unable to open '" + input_name + "' for input")
            return None
        return song_data


def main():
    Logger.initLogging()
    if len(sys.argv) > 1:
        if sys.argv[1] == "--tokens":
            file_name = sys.argv[2]
            ret = TestParse().test_tokens(file_name)
        elif sys.argv[1] == "--midimarks":
            file_name = sys.argv[2]
            ret = TestParse().test_midi_marks(file_name)
        else:
            file_name = sys.argv[1]
            ret = TestParse().test_parse(file_name)
        sys.exit(ret)

if __name__ == "__main__":
    main()
