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

import unittest
from linuxband.mma.bar_chords import BarChords
from linuxband.mma.bar_info import BarInfo
from linuxband.mma.song_data import SongData


class TestBarChords(unittest.TestCase):

    def setUp(self):
        song_data = self.__song_data = SongData([ BarInfo() ], [], 0)
        self.__bar_chords1 = BarChords()
        self.__bar_chords1.set_song_data(song_data)
        self.__bar_chords1.set_chords([['CM7', ' trail1 '], [ 'Am', ' trail2 ']])
        self.__bar_chords2 = BarChords()
        self.__bar_chords2.set_song_data(song_data)
        self.__bar_chords2.set_chords([['CM7', ' trail1 '], [ 'Am', ' trail2 '], [ '/', ' '], ['G', ' trail3 ']])

    def test_set_chord1(self):
        bar_chords = self.__bar_chords1
        bar_chords.set_chord(0, 'A')
        assert bar_chords.get_chords() == [['A', ' trail1 '], [ 'Am', ' trail2 ']]

        bar_chords.set_chord(0, '')
        assert bar_chords.get_chords() == [['/', ' trail1 '], [ 'Am', ' trail2 ']]

        # remove the last chord
        assert '\n' == bar_chords.get_eol()
        bar_chords.set_chord(1, '')
        assert bar_chords.get_chords() == [['/', ' trail1 ']]
        assert ' trail2 \n' == bar_chords.get_eol()

        bar_chords.set_chord(0, '')
        assert bar_chords.get_chords() == [['/', ' trail1 ']]

        bar_chords.set_chord(3, 'BM6')
        assert bar_chords.get_chords() == [['/', ' trail1 '], ['/', ' '], ['/', ' '], ['BM6', '']]

    def test_set_chord2(self):
        bar_chords = self.__bar_chords2

        bar_chords.set_chord(2, 'B')
        assert bar_chords.get_chords() == [['CM7', ' trail1 '], [ 'Am', ' trail2 '], [ 'B', ' '], ['G', ' trail3 ']]

        bar_chords.set_chord(0, '')
        assert bar_chords.get_chords() == [['/', ' trail1 '], [ 'Am', ' trail2 '], [ 'B', ' '], ['G', ' trail3 ']]

        # remove the last chord
        assert '\n' == bar_chords.get_eol()
        bar_chords.set_chord(3, '')
        assert bar_chords.get_chords() == [['/', ' trail1 '], [ 'Am', ' trail2 '], [ 'B', ' ']]
        assert ' trail3 \n' == bar_chords.get_eol()

if __name__ == '__main__':
    # When this module is executed from the command-line, run all its tests
    unittest.main()

