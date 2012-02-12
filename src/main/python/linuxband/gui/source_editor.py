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
import gtk
import gtksourceview2
import pango
import logging
from linuxband.glob import Glob


class SourceEditor(object):

    def __init__(self, glade, song):
        self.__song = song
        self.__init_gui(glade)
        self.__playhead_pos = -1
        self.__error_mark_pos = -1

    def move_playhead_to(self, pos):
        """ Highlight the line just being played. """
        logging.debug("MOVING PLAYHEAD TO %i" % pos)
        buff = self.__sourcebuffer
        # remove the black background and the playhead marker
        start, end = buff.get_bounds()
        buff.remove_tag_by_name("playhead", start, end)
        buff.remove_source_marks(start, end, self.LINE_MARKER)
        # draw the background and the playhead marker again
        if pos > -1:
            iter1 = buff.get_iter_at_line(pos)
            iter2 = buff.get_iter_at_line(pos + 1)
            buff.apply_tag_by_name("playhead", iter1, iter2)
            buff.create_source_mark(None, self.LINE_MARKER, iter1)
        self.__playhead_pos = pos

    def put_error_mark_to(self, line):
        """ Put the red error mark at the beginning of the given line. """
        buff = self.__sourcebuffer
        start, end = buff.get_bounds()
        # remove the red background and the error mark
        buff.remove_tag_by_name("error", start, end)
        buff.remove_source_marks(start, end, self.ERROR_MARKER)
        # draw the red background and the error mark again
        if line > -1:
            # text background redimport logging
            iter1 = buff.get_iter_at_line(line)
            iter2 = buff.get_iter_at_line(line + 1)
            buff.apply_tag_by_name("error", iter1, iter2)
            # error marker    
            it = buff.get_iter_at_line(line)
            buff.create_source_mark(None, self.ERROR_MARKER, it)
        self.__error_mark_pos = line

    def new_song_loaded(self, mma_data):
        self.refresh_source(mma_data)
        self.put_error_mark_to(-1)
        self.__move_cursor_home()

    def refresh_source(self, mma_data):
        """ Loads the new text into the source view, preserves cursor position, preserves marks. """
        buff = self.__sourcebuffer
        # load new text, preserve cursor position
        offset = buff.props.cursor_position
        buff.set_text(mma_data)
        it = buff.get_iter_at_offset(offset)
        buff.place_cursor(it)
        # refresh marks
        self.put_error_mark_to(self.__error_mark_pos)
        self.move_playhead_to(self.__playhead_pos)

    def grab_focus(self):
        gobject.idle_add(self.__gtksourceview.grab_focus)

    def has_focus(self):
        return self.__gtksourceview.is_focus()

    def cut_selection(self):
        buff = self.__sourcebuffer
        buff.cut_clipboard(gtk.clipboard_get(), True)

    def copy_selection(self):
        buff = self.__sourcebuffer
        buff.copy_clipboard(gtk.clipboard_get())

    def paste_selection(self):
        buff = self.__sourcebuffer
        buff.paste_clipboard(gtk.clipboard_get(), None, True)

    def delete_selection(self):
        buff = self.__sourcebuffer
        buff.delete_selection(False, True)

    def select_all(self):
        buff = self.__sourcebuffer
        buff.select_range(buff.get_start_iter(), buff.get_end_iter())

    def __init_gui(self, glade):
        scrolledwindow6 = glade.get_widget("scrolledwindow6")

        self.__gtksourceview = gtksourceview2.View()
        self.__sourcebuffer = gtksourceview2.Buffer()

        view = self.__gtksourceview
        buff = self.__sourcebuffer

        view.set_buffer(buff)
        scrolledwindow6.add(view)

        view.set_auto_indent(True)
        view.set_highlight_current_line(True)
        view.set_show_line_numbers(True)
        view.set_show_line_marks(True)
        view.set_show_right_margin(True)
        view.set_insert_spaces_instead_of_tabs(True)
        view.set_tab_width(4)
        view.set_indent_width(-1)
        view.set_right_margin_position(80)
        view.set_smart_home_end(True)
        view.set_indent_on_tab(True)
        view.set_left_margin(2)
        view.set_right_margin(2)
        view.modify_font(pango.FontDescription("mono 10"))
        view.set_wrap_mode(gtk.WRAP_NONE)
        # playhead text attributes
        tag = buff.create_tag("playhead")
        tag.props.background = "black"
        tag.props.background_set = True
        tag.props.foreground = "white"
        tag.props.foreground_set = True
        # error text attributes
        tag = buff.create_tag("error")
        tag.props.background = "red"
        tag.props.background_set = True
        # playhead marker
        self.LINE_MARKER = 'lineMarker'
        pixbuf = gtk.gdk.pixbuf_new_from_file(Glob.LINE_MARKER)
        view.set_mark_category_pixbuf(self.LINE_MARKER, pixbuf)
        # error marker
        self.ERROR_MARKER = 'errorMarker'
        pixbuf = gtk.gdk.pixbuf_new_from_file(Glob.ERROR_MARKER)
        view.set_mark_category_pixbuf(self.ERROR_MARKER, pixbuf)
        # buff parameters
        buff.set_highlight_syntax(True)
        buff.set_highlight_matching_brackets(True)
        buff.set_max_undo_levels(50)
        # when buff modified save needed
        buff.connect("modified-changed", self.__modified_changed)
        # and show it
        self.__gtksourceview.show()

    def __modified_changed(self, buff):
        if self.__gtksourceview.is_focus():
            buff = self.__sourcebuffer
            mma_data = buff.get_text(buff.get_start_iter(), buff.get_end_iter())
            self.__song.load_from_string(mma_data)
        buff.set_modified(False)

    def __move_cursor_home(self):
        buff = self.__sourcebuffer
        it = buff.get_iter_at_offset(0)
        buff.place_cursor(it)
