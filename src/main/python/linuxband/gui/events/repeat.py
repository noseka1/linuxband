# -*- coding: utf-8 -*-

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


class EventRepeat(object):

    def __init__(self, glade):
        pass

    def set_label_from_event(self, button, event):
        """ Sets the label of Repeat button. """
        button.set_label("Repeat")

    def get_new_event(self):
        return None

    def init_window(self, button, data):
        pass
