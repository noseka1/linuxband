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

import os


class Glob:

    # action constants in alphabet order
    A_AUTHOR = "AUTHOR"
    A_BEGIN_BLOCK = "BEGINBLOCK"
    A_DEF_GROOVE = "DEFGROOVE"
    A_DOC = "DOC"
    A_GROOVE = "GROOVE"
    A_REMARK = "REMARK" # comment line with song title
    A_REPEAT = "REPEAT"
    A_REPEAT_END = "REPEATEND"
    A_REPEAT_ENDING = "REPEATENDING"
    A_TEMPO = "TEMPO"
    A_TIME = "TIME"
    A_TIME_SIG = "TIMESIG"
    A_UNKNOWN = "UNKNOWN"

    # list of supported events, order of Add event menulist
    EVENTS = [ A_GROOVE, A_TEMPO, A_REPEAT, A_REPEAT_ENDING, A_REPEAT_END ]

    OUTPUT_FILE_DEFAULT = "untitled.mma"
    UNTITLED_SONG_NAME = "Untitled Song"

        # user's home dir - works for windows/unix/linux
    HOME_DIR = os.getenv('USERPROFILE') or os.getenv('HOME')
    CONFIG_DIR = HOME_DIR + '/.linuxband'

    PID = os.getpid()

    # will be set by main function
    PACKAGE_VERSION = ""
    PACKAGE_BUGREPORT = ""
    PACKAGE_URL = ""
    PACKAGE_TITLE = ""
    PACKAGE_COPYRIGHT = ""
    LINE_MARKER = ""
    ERROR_MARKER = ""
    DEFAULT_CONFIG_FILE = ""
    GLADE = ""
    LICENSE = ""
    PLAYER_PROGRAM = ""
    CONSOLE_LOG_LEVEL = None

