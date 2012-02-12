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

import logging
from linuxband.gui.common import Common
from linuxband.glob import Glob


class AboutDialog(object):

    def __init__(self, glade):
        dialog = self.__about_dialog = glade.get_widget("aboutDialog")
        dialog.set_program_name(Glob.PACKAGE_TITLE)
        dialog.set_version(Glob.PACKAGE_VERSION)
        dialog.set_copyright(Glob.PACKAGE_COPYRIGHT + ', ' + Glob.PACKAGE_BUGREPORT)
        dialog.set_website(Glob.PACKAGE_URL)
        fname = Glob.LICENSE
        license_text = ''
        try:
            infile = file(fname, 'r')
            try:
                license_text = infile.read()
            finally:
                infile.close()
        except:
            logging.exception("Unable to read license file '" + fname + "'")
        dialog.set_license(license_text)
        Common.connect_signals(glade, self)

    def help_about_callback(self, menuitem):
        self.__about_dialog.present()

    def about_dialog_response_callback(self, dialog, response):
        self.__about_dialog.hide()
        return True

    def about_dialog_delete_event_callback(self, dialog, event):
        self.__about_dialog.hide()
        return True
