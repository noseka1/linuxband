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
from linuxband.glob import Glob


class BarInfo:

    def __init__(self):
        self.__song_data = None
        self.__lines = []
        self.__events = []

    def set_song_data(self, song_data):
        self.__song_data = song_data

    def add_line(self, line):
        self.__lines.append(line)
        if line[0] in Glob.EVENTS:
            self.__events.append(line)

    def insert_line(self, line):
        """ The same as add_line but inserting at the beginning """
        self.__lines.insert(0, line)
        if line[0] in Glob.EVENTS:
            self.__events.insert(0, line)

    def get_events(self):
        return self.__events

    # methods used by ChordSheet    
    def has_events(self):
        return True if len(self.__events) > 0 else False

    def has_repeat_begin(self):
        return self.__lookup_action(Glob.A_REPEAT) != None

    def has_repeat_end(self):
        return self.__lookup_action(Glob.A_REPEAT_ENDING) or self.__lookup_action(Glob.A_REPEAT_END)

    def show_debug(self):
        for i, v in enumerate(self.__lines):
            logging.debug("%i %s ", i, v)

    def get_groove(self):
        return self.__lookup_action(Glob.A_GROOVE)

    def get_tempo(self):
        return self.__lookup_action(Glob.A_TEMPO)

    def get_lines(self):
        return self.__lines

    def add_event(self, line):
        if line[0] in [ Glob.A_REPEAT_END, Glob.A_REPEAT_ENDING ]:
            self.insert_line(line)
        else:
            self.add_line(line)
        self.__song_data.changed()

    def remove_event(self, line):
        self.__lines.remove(line)
        self.__events.remove(line)
        self.__song_data.changed()

    def replace_event(self, old, new):
        index = self.__find_element(self.__lines, old)
        self.__lines[index] = new
        index = self.__find_element(self.__events, old)
        self.__events[index] = new
        self.__song_data.changed()

    def move_event_backwards(self, line):
        index = self.__events.index(line)
        if index > 0:
            previous = self.__events[index - 1]
            self.__swap_events(line, previous, self.__lines)
            self.__swap_events(line, previous, self.__events)
            self.__song_data.changed()

    def move_event_forwards(self, line):
        index = self.__events.index(line)
        if index < len(self.__events) - 1:
            next_event = self.__events[index + 1]
            self.__swap_events(line, next_event, self.__lines)
            self.__swap_events(line, next_event, self.__events)
            self.__song_data.changed()

    def get_as_string_list(self):
        res = []
        for line in self.__lines:
            if line[0] == Glob.A_BEGIN_BLOCK:
                res.extend(line[2:])
            else:
                res.extend(line[1:])
        return res

    def __lookup_action(self, action):
        for item in self.__lines:
            if item[0] == action:
                return item
        return None

    def __find_element(self, lst, elem):
        for index in range(0, len(lst)):
            if lst[index] is elem:
                return index

    def __swap_events(self, event1, event2, lst):
        index1 = lst.index(event1)
        index2 = lst.index(event2)
        lst[index1] = event2
        lst[index2] = event1

    def __deepcopy__(self, memo):
        newone = BarInfo()
        newone.__song_data = self.__song_data
        newone.__lines = copy.deepcopy(self.__lines, memo)
        newone.__events = copy.deepcopy(self.__events, memo)
        return newone

    @staticmethod
    def create_event(eventTitle):
        eventsInit = { Glob.A_GROOVE:       [ Glob.A_GROOVE, "Groove", " ", "50sRock", "\n" ],
                       Glob.A_TEMPO:        [ Glob.A_TEMPO, "Tempo", " ", "120", "\n" ],
                       Glob.A_REPEAT:       [ Glob.A_REPEAT, "Repeat", "\n" ],
                       Glob.A_REPEAT_ENDING: [ Glob.A_REPEAT_ENDING, "RepeatEnding", "\n" ],
                       Glob.A_REPEAT_END:    [ Glob.A_REPEAT_END, "RepeatEnd", "\n" ] }
        return copy.deepcopy(eventsInit[eventTitle])

    @staticmethod
    def set_groove_value(line, groove):
        line[3] = groove

    @staticmethod
    def get_groove_value(line):
        return line[3]

    @staticmethod
    def set_tempo_value(line, tempo):
        line[3] = tempo

    @staticmethod
    def get_tempo_value(line):
        return line[3]

    @staticmethod
    def set_repeat_end_value(line, count):
        # example line: ['REPEATEND', 'RepeatEnd', ' ', '2', '\n']
        if len(line) > 3: # there is already some number
            if count == 2:
                line.pop(2)
                line.pop(2)
            else:
                line[3] = count
        else: # no number yet, example: ['REPEATEND', 'RepeatEnd', '\n']
            if count != 2:
                line.insert(2, count)
                line.insert(2, ' ')

    @staticmethod
    def get_repeat_end_value(line):
        return line[3] if len(line) > 3 else "2"

    @staticmethod
    def set_repeat_ending_value(line, count):
        BarInfo.set_repeat_end_value(line, count)

    @staticmethod
    def get_repeat_ending_value(line):
        return BarInfo.get_repeat_end_value(line)

    @staticmethod
    def get_doc_value(line):
        res = line[3]
        res = res.split()
        res = ' '.join(res)
        return res

    @staticmethod
    def get_author_value(line):
        return line[2].strip()

    @staticmethod
    def get_time_value(line):
        return line[2]

    @staticmethod
    def get_defgroove_value(line):
        return line[3], ' '.join(line[4].replace('\\\n', '').split())
