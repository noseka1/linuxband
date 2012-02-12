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

from linuxband.glob import Glob
from linuxband.mma.bar_info import BarInfo
from linuxband.gui.common import Common


class EventTempo(object):

    __TEMPO_UNDEFINED = "Select tempo"

    def __init__(self, glade):
        self.__toggled_button = None
        self.__curr_event = None
        self.__new_event = None
        self.__init_gui(glade)

    def on_spinbutton2_value_changed_callback(self, spinbutton):
        """ Tempo changed """
        count = str(int(spinbutton.get_value()))
        event = BarInfo.create_event(Glob.A_TEMPO)
        BarInfo.set_tempo_value(event, count)
        self.set_label_from_event(self.__toggled_button, event)
        self.__new_event = event

    def set_label_from_event(self, button, event):
        """ Set the label of tempo button correctly
            even if the event in the self.__song.get_data().get_bar_info(0) is missing """
        if event:
            label = BarInfo.get_tempo_value(event) + ' BPM'
            button.set_label(label)
        else:
            button.set_label(EventTempo.__TEMPO_UNDEFINED)

    def get_new_event(self):
        return self.__new_event

    def init_window(self, button, event):
        # hide back, forward, remove buttons
        if button is self.__togglebutton2: self.__alignment15.hide()
        else: self.__alignment15.show()
        self.__toggled_button = button
        self.__curr_event = event
        self.__new_event = None
        if event:
            self.__spinbutton2.set_value(int(BarInfo.get_tempo_value(event)))
        else:
            self.on_spinbutton2_value_changed_callback(self.__spinbutton2)
        self.__spinbutton2.grab_focus()

    def __init_gui(self, glade):
        Common.connect_signals(glade, self)
        # back, forward, remove event buttons will be hidden
        self.__alignment15 = glade.get_widget("alignment15")
        self.__togglebutton2 = glade.get_widget("togglebutton2")
        self.__spinbutton2 = glade.get_widget("spinbutton2")
