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

import gobject


class SaveButtonStatus(object):

    def __init__(self, glade, song):
        button = glade.get_widget("toolbutton9")
        menuitem = glade.get_widget("imagemenuitem3")
        mainwindow = glade.get_widget("mainWindow")
        self.__sourceId = gobject.timeout_add(800, self.__refresh_save_button_status, song, button, menuitem, mainwindow)

    def __refresh_save_button_status(self, song, button, menuitem, mainwindow):
        save_needed = song.get_data().is_save_needed()
        button.set_sensitive(save_needed)
        menuitem.set_sensitive(save_needed)
        prefix = "*"  if save_needed else ""
        mainwindow.set_title(prefix + song.get_data().get_title() + " | Linux Band")
        return True
