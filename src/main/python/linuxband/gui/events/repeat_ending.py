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

import gtk
from linuxband.glob import Glob
from linuxband.mma.bar_info import BarInfo
from linuxband.gui.common import Common


class EventRepeatEnding(object):

    def __init__(self, glade):
        self.__toggled_button = None
        self.__curr_event = None
        self.__new_event = None
        self.__init_gui(glade)

    def on_comboboxentry2_changed_callback(self, widget):
        """ RepeatEnding value changed """
        # called also when initializing the entries list
        if not self.__toggled_button: return
        try:
            i = int(widget.child.get_text())
        except ValueError:
            return
        count = str(i)
        event = BarInfo.create_event(Glob.A_REPEAT_ENDING)
        BarInfo.set_repeat_ending_value(event, count)
        self.set_label_from_event(self.__toggled_button, event)
        self.__new_event = event

    def set_label_from_event(self, button, event):
        """ Sets the label of RepeatEnding button when the count was changed """
        count = BarInfo.get_repeat_ending_value(event)
        if count == "2": label = "RepeatEnding"
        else: label = "RepeatEnding " + count
        button.set_label(label)

    def get_new_event(self):
        return self.__new_event

    def init_window(self, button, event):
        self.__toggled_button = button
        self.__curr_event = event
        self.__new_event = None
        text = BarInfo.get_repeat_ending_value(event)
        self.__entry.set_text(text)
        self.__combobox_entry.grab_focus()

    def __init_gui(self, glade):
        Common.connect_signals(glade, self)
        # RepeatEnding entry
        self.__combobox_entry = glade.get_widget("comboboxentry2")
        self.__entry = self.__combobox_entry.child
        combobox = self.__combobox_entry
        list_store = gtk.ListStore(str)
        combobox.set_model(list_store)
        for i in range(2, 6):
            combobox.append_text(str(i))
        combobox.set_active(0)
