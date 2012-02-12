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

from linuxband.gui.common import Common
import gtk

class Preferences(object):

    def __init__(self, glade, gui, config, grooves):
        self.__gui = gui
        self.__config = config
        self.__grooves = grooves
        self.__init_gui(glade)

    def run(self):
        self.__initWidgets();
        result = self.__preferencesdialog.run()
        self.__preferencesdialog.hide()
        if (result == gtk.RESPONSE_OK):
            self.__apply_changes()
            self.__config.save_config()

    def __init_gui(self, glade):
        Common.connect_signals(glade, self)
        self.__preferencesdialog = glade.get_widget("preferencesDialog")
        self.__filechooserbutton1 = glade.get_widget("filechooserbutton1")
        self.__filechooserbutton2 = glade.get_widget("filechooserbutton2")
        self.__fontbutton1 = glade.get_widget("fontbutton1")
        self.__checkbutton2 = glade.get_widget("checkbutton2")

    def __initWidgets(self):
        self.__filechooserbutton1.set_filename(self.__config.get_mma_path())
        self.__filechooserbutton2.set_filename(self.__config.get_mma_grooves_path())
        self.__fontbutton1.set_font_name(self.__config.get_chord_sheet_font())
        self.__checkbutton2.set_active(self.__config.get_jack_connect_startup())

    def __apply_changes(self):
        # path to mma
        self.__config.set_mma_path(self.__filechooserbutton1.get_filename())
        # path to grooves
        new_mma_grooves_path = self.__filechooserbutton2.get_filename()
        if (self.__config.get_mma_grooves_path() != new_mma_grooves_path):
            self.__config.set_mma_grooves_path(new_mma_grooves_path)
            self.__grooves.load_grooves(False)
        # chord sheet font
        new_chord_sheet_font = self.__fontbutton1.get_font_name()
        if (self.__config.get_chord_sheet_font() != new_chord_sheet_font):
            self.__config.set_chord_sheet_font(new_chord_sheet_font)
            self.__gui.refresh_chord_sheet()
        # connect to JACK on startup
        self.__config.set_jack_connect_startup(self.__checkbutton2.get_active())
