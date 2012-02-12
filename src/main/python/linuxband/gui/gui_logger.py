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
import traceback


class GuiLogger(object):

    class __TextBufferHandler(logging.Handler):

        def __init__(self, textView, textBuffer):
            logging.Handler.__init__(self)
            self.__textView = textView
            self.__textBuffer = textBuffer

        def emit(self, record):
            record.exc_text = None # is needed to formatException to be called

            if record.levelname == 'INFO': tag = 'fg_black'
            elif record.levelname == 'WARNING': tag = 'fg_brown'
            elif record.levelname == 'ERROR': tag = 'fg_red'

            start, end = self.__textBuffer.get_bounds() #@UnusedVariable
            text = self.__textBuffer.get_text(start, end)
            eol = '' if text == '' else '\n'

            mark = self.__textBuffer.create_mark(None, end, False)
            self.__textBuffer.insert_with_tags_by_name(end, eol + self.format(record), tag)
            self.__textView.scroll_to_mark(mark, 0, True, 0.0, 1.0)
            self.__textBuffer.delete_mark(mark)

    class __MyFormatter(logging.Formatter):

        def __init__(self, fmt=None, datefmt=None):
            logging.Formatter.__init__(self, fmt, datefmt)

        def formatException(self, ei):
            excType, excValue, excTraceback = ei #@UnusedVariable
            res = ''.join(traceback.format_exception_only(excType, excValue))
            if res[-1] == '\n':
                res = res[:-1]
            return res

    @staticmethod
    def initLogging(glade):
        textView = glade.get_widget("textview1")
        textBuffer = textView.get_buffer()
        GuiLogger.__createColorTags(textView, textBuffer)
        GuiLogger.__configureLogging(textView, textBuffer)

    @staticmethod
    def __createColorTags(textView, textBuffer):
        colormap = textView.get_colormap()
        color = colormap.alloc_color('red')
        textBuffer.create_tag('fg_red', foreground_gdk=color)
        color = colormap.alloc_color('brown');
        textBuffer.create_tag('fg_brown', foreground_gdk=color)
        color = colormap.alloc_color('black');
        textBuffer.create_tag('fg_black', foreground_gdk=color)

    @staticmethod
    def __configureLogging(textView, textBuffer):
        guiFormat = "%(asctime)s %(levelname)s %(message)s"
        dateFormat = "%H:%M:%S"
        textBufferHandler = GuiLogger.__TextBufferHandler(textView, textBuffer)
        textBufferHandler.setLevel(logging.INFO)
        textBufferHandler.setFormatter(GuiLogger.__MyFormatter(guiFormat, dateFormat))
        rootLogger = logging.getLogger();
        rootLogger.addHandler(textBufferHandler)
