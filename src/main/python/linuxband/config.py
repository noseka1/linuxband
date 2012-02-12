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

import ConfigParser
import logging
from linuxband.glob import Glob
import os


class Config(object):

    __rc_file = Glob.CONFIG_DIR + '/linuxband.rc'
    __home_dir = Glob.HOME_DIR
    __default_config = Glob.DEFAULT_CONFIG_FILE

    __SAVED = "Saved"
    __PREFERENCES = "Preferences"
    __MMA_PATH = "mma_path"
    __MMA_GROOVES_PATH = "mma_grooves_path"
    __CHORD_SHEET_FONT = "chord_sheet_font"
    __JACK_CONNECT_STARTUP = "jack_connect_startup"
    __TEMPLATE_FILE = "template_file"
    __WORK_DIR = "work_dir"
    __LOOP = "loop"
    __JACK_TRANSPORT = "jack_transport"
    __INTRO_LENGTH = "intro_length"

    def __init__(self):
        self.__config = ConfigParser.SafeConfigParser()

    def load_config(self):
        if self.__ensure_dir(Glob.CONFIG_DIR):
            try:
                logging.debug("Opening config")
                self.__config.read(Config.__rc_file)
            except:
                logging.exception("Error reading configuration file '%s', loading defaults." % Config.__rc_file)
                self.__load_default_config()
        else:
            self.__load_default_config()
            self.save_config()

    def save_config(self):
        """
        Save configuration into file.
        """
        fname = Config.__rc_file
        logging.info("Saving configuration to '" + fname + "'")
        try:
            out_file = file(fname, 'w')
            try:
                self.__config.write(out_file)
            finally:
                out_file.close()
        except:
            logging.exception("Unable to save configuration file '" + fname + "'")

    def get_work_dir(self):
        return self.__config.get(Config.__SAVED, Config.__WORK_DIR)

    def set_work_dir(self, work_dir):
        self.__config.set(Config.__SAVED, Config.__WORK_DIR, work_dir)

    def get_jack_transport(self):
        return self.__config.getboolean(Config.__SAVED, Config.__JACK_TRANSPORT)

    def set_jack_transport(self, value):
        self.__config.set(Config.__SAVED, Config.__JACK_TRANSPORT, str(value))

    def get_loop(self):
        return self.__config.getboolean(Config.__SAVED, Config.__LOOP)

    def set_loop(self, value):
        self.__config.set(Config.__SAVED, Config.__LOOP, str(value))

    def get_intro_length(self):
        return self.__config.getint(Config.__SAVED, Config.__INTRO_LENGTH)

    def set_intro_length(self, value):
        self.__config.set(Config.__SAVED, Config.__INTRO_LENGTH, str(value))

    def getTemplateFile(self):
        return self.__config.get(Config.__PREFERENCES, Config.__TEMPLATE_FILE)

    def setTemplateFile(self, file_name):
        self.__config.set(Config.__PREFERENCES, Config.__TEMPLATE_FILE, file_name)

    def get_mma_path(self):
        return self.__config.get(Config.__PREFERENCES, Config.__MMA_PATH)

    def set_mma_path(self, mma_path):
        self.__config.set(Config.__PREFERENCES, Config.__MMA_PATH, mma_path)

    def get_mma_grooves_path(self):
        return self.__config.get(Config.__PREFERENCES, Config.__MMA_GROOVES_PATH)

    def set_mma_grooves_path(self, path):
        self.__config.set(Config.__PREFERENCES, Config.__MMA_GROOVES_PATH, path)

    def get_jack_connect_startup(self):
        return self.__config.getboolean(Config.__PREFERENCES, Config.__JACK_CONNECT_STARTUP)

    def set_jack_connect_startup(self, connect):
        self.__config.set(Config.__PREFERENCES, Config.__JACK_CONNECT_STARTUP, str(connect))

    def get_chord_sheet_font(self):
        return self.__config.get(Config.__PREFERENCES, Config.__CHORD_SHEET_FONT)

    def set_chord_sheet_font(self, font):
        self.__config.set(Config.__PREFERENCES, Config.__CHORD_SHEET_FONT, font)

    def __load_default_config(self):
        try:
            self.__config.read(Config.__default_config)
            self.set_work_dir(Config.__home_dir)
        except:
            logging.exception("Failed to read default configuration from '" + Config.__default_config + "'")

    def __ensure_dir(self, newdir):
        """
        If the directory already exists return True. Else try to create it and return False.
        """
        if os.path.isdir(newdir):
            return True
        try:
            os.mkdir(newdir)
        except:
            logging.exception("Unable to create directory '" + newdir + "'")
        return False
