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
import pango
import copy
from gtk.gdk import CONTROL_MASK, SHIFT_MASK, BUTTON1_MASK
import logging
from linuxband.mma.bar_chords import BarChords
from linuxband.mma.bar_info import BarInfo
from linuxband.gui.common import Common


class ChordSheet(object):

    __bar_height = 40
    __cell_padding = 2
    __max_bar_chords_font = 40
    __bars_per_line = 4

    __color_no_song = "honeydew3"
    __color_playhead = "black"
    __color_selection = "SteelBlue"
    __color_cursor = "yellow"
    __color_events = "grey73"
    __color_song = "honeydew2"

    def __init__(self, glade, song, gui, config):
        self.__song = song
        self.__cursor_pos = 0
        self.__end_position = 0
        self.__playhead_pos = -1
        self.__selection_start = None
        self.__selection = set([])
        self.__clipboard = []
        self.__gui = gui
        self.__config = config
        self.__init_gui(glade)

    def drawing_area_realize_event_callback(self, widget):
        self.drawable = self.__area.window
        self.gc = self.drawable.new_gc()
        # Create a new backing pixmap of the appropriate size
        self.pixmap = gtk.gdk.Pixmap(self.drawable, self.__drawing_area_width, self.__drawing_area_height, depth= -1)
        gc = self.drawable.new_gc()
        gc.copy(self.gc)
        green = self.__colormap.alloc_color(ChordSheet.__color_no_song, True, True)
        gc.set_foreground(green)
        self.pixmap.draw_rectangle(gc, True, 0, 0, self.__drawing_area_width, self.__drawing_area_height)
        return True

    def drawing_area_expose_event_callback(self, widget, event):
        """ Redraw the screen from the backing pixmap. """
        x , y, width, height = event.area
        widget.window.draw_drawable(widget.get_style().fg_gc[gtk.STATE_NORMAL],
        self.pixmap, x, y, x, y, width, height)
        return True

    def move_playhead_to(self, pos):
        new_pos = pos * 2 + 1 if pos > -1 else -1
        old_pos = self.__playhead_pos
        if  old_pos != new_pos:
            self.__playhead_pos = new_pos
            self.__render_field(old_pos)
            self.__render_field(new_pos)

    def drawing_area_keypress_event_callback(self, widget, event):
        key = event.keyval
        old_pos = self.__cursor_pos
        if key == gtk.keysyms.Left or key == gtk.keysyms.h or key == gtk.keysyms.H:
            targetPos = self.__cursor_pos - 1
            if targetPos >= 0:
                self.__move_cursor_to(targetPos)
        elif key == gtk.keysyms.Right or key == gtk.keysyms.l or key == gtk.keysyms.L:
            self.__move_cursor_to(self.__cursor_pos + 1)
        elif key == gtk.keysyms.Up or key == gtk.keysyms.k or key == gtk.keysyms.K:
            targetPos = self.__cursor_pos - ChordSheet.__bars_per_line * 2
            if targetPos >= 0:
                self.__move_cursor_to(targetPos)
        elif key == gtk.keysyms.Down or key == gtk.keysyms.j or key == gtk.keysyms.J:
            self.__move_cursor_to(self.__cursor_pos + ChordSheet.__bars_per_line * 2)
        elif key == gtk.keysyms.Home:
            self.__move_cursor_to(0)
        elif key == gtk.keysyms.End:
            self.__move_cursor_to(self.__end_position)
        elif event.state & CONTROL_MASK and key == gtk.keysyms.Delete:
            self.cut_selection()
        elif event.state & CONTROL_MASK and key == gtk.keysyms.Insert:
            self.copy_selection()
        elif event.state & SHIFT_MASK and key == gtk.keysyms.Insert:
            self.paste_selection()
        elif key == gtk.keysyms.Delete:
            self.delete_selection()
        # move focus to chord entries
        elif self.__is_bar_chords(self.__cursor_pos):
            if key == gtk.keysyms.Return:
                self.__move_cursor_to(self.__cursor_pos + 2)
                self.__destroy_selection()
        # adjust selection
        if key in [ gtk.keysyms.Left, gtk.keysyms.Right, gtk.keysyms.Up, gtk.keysyms.Down,
                         gtk.keysyms.Home, gtk.keysyms.End ]:
            if event.state & SHIFT_MASK:
                self.__adjust_selection(old_pos)
            else:
                self.__destroy_selection()
        if key in [ gtk.keysyms.H, gtk.keysyms.L, gtk.keysyms.K, gtk.keysyms.J ]:
            self.__adjust_selection(old_pos)
        if key in [ gtk.keysyms.h, gtk.keysyms.l, gtk.keysyms.k, gtk.keysyms.j ]:
            self.__destroy_selection()
        # the event has been handled
        return True

    def cut_selection(self):
        """ Put selected fields from area into clipboard and delete them. """
        self.copy_selection()
        self.delete_selection()

    def copy_selection(self):
        """ Copy selected fields from area into clipboard. """
        if len(self.__selection) == 0:
            sel = set([self.__cursor_pos])
        else:
            sel = self.__selection
        self.__clipboard = []
        for field_num in sorted(sel):
            bar_num = field_num / 2
            if self.__is_bar_chords(field_num):
                self.__clipboard.append(copy.deepcopy(self.__song.get_data().get_bar_chords(bar_num)))
            else:
                self.__clipboard.append(copy.deepcopy(self.__song.get_data().get_bar_info(bar_num)))

    def paste_selection(self):
        """ Paste fields from the clipboard. """
        clipboard = list(self.__clipboard)
        length = len(clipboard)
        if length > 0:
            if isinstance(clipboard[0], BarChords) and self.__is_bar_info(self.__cursor_pos):
                logging.warning("cannot paste chords on bar-info")
                return
            elif isinstance(clipboard[0], BarInfo) and self.__is_bar_chords(self.__cursor_pos):
                logging.warning("cannot paste bar-info on chords")
                return
            self.__destroy_selection()
            old_pos = self.__cursor_pos
            new_pos = old_pos + length - 1
            self.__move_cursor_to(new_pos) # if needed new fields will be appended
            bar_num = old_pos / 2
            for field in clipboard:
                if isinstance(field, BarChords):
                    self.__song.get_data().set_bar_chords(bar_num, field)
                    bar_num = bar_num + 1
                else:
                    self.__song.get_data().set_bar_info(bar_num, field)
            self.__adjust_selection(old_pos) # refreshes affected fields
            if old_pos > 0: self.__render_field(old_pos - 1) # refresh barNumber

    def delete_selection(self):
        """ Delete selected fields """
        if len(self.__selection) == 0:
            sel = set([self.__cursor_pos])
        else:
            sel = self.__selection
        for field_num in sorted(sel):
            bar_num = field_num / 2
            if self.__is_bar_chords(field_num):
                self.__song.get_data().set_bar_chords(bar_num, self.__song.get_data().create_bar_chords())
            else:
                self.__song.get_data().set_bar_info(bar_num, self.__song.get_data().create_bar_info())
        # refresh deleted fields + possible bar_info at the beginning
        for field_num in sel:
            self.__render_field(field_num)
        m = min(sel)
        if m > 0: self.__render_field(m - 1)
        # if deleted bars from the end, shorten the song
        if max(sel) == self.__end_position:
            first = min(sel)
            if self.__is_bar_info(first):
                if (first + 1) in sel:
                    first = first + 1
            if self.__is_bar_chords(first):
                bar_num = first / 2
                self.__gui.change_song_bar_count(bar_num)
        self.__refresh_entries_and_events()

    def select_all(self):
        self.__move_cursor_to(self.__end_position)
        self.__adjust_selection(0)

    def get_selection_limits(self):
        """ Selection start and end bar numbers """
        if self.__selection:
            return min(self.__selection) / 2, max(self.__selection) / 2
        else:
            return self.__cursor_pos / 2, self.__cursor_pos / 2

    def drawing_area_clicked(self, widget, event):
        if event.button == 1:
            old_pos = self.__cursor_pos
            pos = self.__locate_mouse_click(event.x, event.y)
            self.__move_cursor_to(pos)
            if event.state & SHIFT_MASK:
                self.__adjust_selection(old_pos)
            else:
                self.__destroy_selection()
            self.__area.grab_focus()

    def drawing_area_motion_notify_event_callback(self, widget, event):
        # selection by mouse
        if event.state & BUTTON1_MASK:
            pos = self.__locate_mouse_click(event.x, event.y)
            old_pos = self.__cursor_pos
            if not pos == old_pos:
                self.__move_cursor_to(pos)
                self.__adjust_selection(old_pos)
        return False

    def grab_focus(self):
        self.__area.grab_focus()

    def has_focus(self):
        return self.__area.is_focus()

    def change_song_bar_count(self, bar_count):
        new_end = bar_count * 2
        if new_end == self.__end_position:
            return
        elif new_end > self.__end_position: # render affected fields
            fields_to_render = range(self.__end_position, new_end + 1)
            for field in fields_to_render: self.__render_field(field)
        elif new_end < self.__end_position:
            fields_to_render = range(new_end, self.__end_position + 1)
            for field in fields_to_render: self.__render_field(field)
        self.__end_position = new_end

        if new_end == 0:
            self.__cursor_pos = 0
        elif self.__cursor_pos > new_end:
            self.__cursor_pos = new_end

        self.__move_cursor_to(self.__cursor_pos)
        self.__adjust_selection_bar_count_changed()

    def set_song_bar_count(self, bar_count):
        new_end = bar_count * 2
        maxlast = max(self.__end_position, new_end)
        fields_to_render = range(0, maxlast + 1)
        for field in fields_to_render: self.__render_field(field)
        self.__end_position = new_end

        if new_end == 0:
            self.__cursor_pos = 0
        elif self.__cursor_pos > new_end:
            self.__cursor_pos = new_end

        self.__move_cursor_to(self.__cursor_pos)
        self.__adjust_selection_bar_count_changed()

    def is_cursor_on_bar_info(self):
        return self.__is_bar_info(self.__cursor_pos)

    def is_cursor_on_bar_chords(self):
        return self.__is_bar_chords(self.__cursor_pos)

    def get_current_bar_number(self):
        return self.__cursor_pos / 2

    def new_song_loaded(self):
        self.__move_cursor_to(0) # cursor on field 0 => global buttons get refreshed
        self.__destroy_selection()

    def render_current_field(self, chords=None):
        self.__render_field(self.__cursor_pos, chords)

    def chord_entry_editing_finished(self):
        self.grab_focus()
        self.__move_cursor_to(self.__cursor_pos + 2)
        self.__destroy_selection()

    def __init_gui(self, glade):
        Common.connect_signals(glade, self)
        self.__area = glade.get_widget("drawingarea1")
        self.__colormap = self.__area.get_colormap()
        self.__drawing_area_width, self.__drawing_area_height = self.__area.get_size_request()
        self.__bar_width = self.__drawing_area_width / self.__song.get_data().get_beats_per_bar()
        self.__bar_chords_width = self.__bar_width * 9 / 10
        self.__bar_info_width = self.__bar_width - self.__bar_chords_width
        self.__area.show()

    def __render_chord_xy(self, chord, x, y, width, height, playhead):
        """ Render one chord on position x,y. """
        if playhead: color = self.__colormap.alloc_color('white')
        else: color = self.__colormap.alloc_color('black')
        gc = self.pixmap.new_gc()
        gc.copy(self.gc)
        #gc.set_line_attributes(1, gtk.gdk.LINE_SOLID, gtk.gdk.CAP_ROUND, gtk.gdk.JOIN_ROUND)
        gc.set_foreground(color)
        #self.pixmap.draw_rectangle(gc, False, x , y, width, height)

        pango_layout = self.__area.create_pango_layout("")
        pango_layout.set_text(chord)
        fd = pango.FontDescription(self.__config.get_chord_sheet_font())

        size = (ChordSheet.__max_bar_chords_font + 1) * pango.SCALE
        while True:
            size = size - pango.SCALE
            fd.set_size(size)
            pango_layout.set_font_description(fd)
            text_width, text_height = pango_layout.get_pixel_size()
            if text_width <= width and text_height <= height:
                break

        ink, logical = pango_layout.get_pixel_extents() #@UnusedVariable
        self.pixmap.draw_layout(gc, x, y + (height - ink[1] - ink[3]), pango_layout)

    def __render_chords_xy(self, bar_num, chords, bar_x, bar_y, playhead, cursor, selection):
        if bar_num >= self.__song.get_data().get_bar_count():
            color_code = ChordSheet.__color_no_song
        elif playhead:
            color_code = ChordSheet.__color_playhead
        elif selection:
            color_code = ChordSheet.__color_selection
        elif cursor:
            color_code = ChordSheet.__color_cursor
        else:
            color_code = ChordSheet.__color_song

        color = self.__colormap.alloc_color(color_code)
        gc = self.pixmap.new_gc()
        gc.copy(self.gc)
        gc.set_foreground(color)
        self.pixmap.draw_rectangle(gc, True, bar_x , bar_y, self.__bar_chords_width, ChordSheet.__bar_height)
        if cursor: # black border
            color = self.__colormap.alloc_color("black")
            gc.set_foreground(color)
            self.pixmap.draw_rectangle(gc, False, bar_x , bar_y, self.__bar_chords_width - 1, ChordSheet.__bar_height - 1)

        if not chords:
            return

        if playhead:
            color = self.__colormap.alloc_color("white")
        else:
            color = self.__colormap.alloc_color("black")
        gc.set_foreground(color)

        bar_chords_width = self.__bar_chords_width - (self.__song.get_data().get_beats_per_bar()) * ChordSheet.__cell_padding
        bar_chords_height = ChordSheet.__bar_height - 2 * ChordSheet.__cell_padding
        chord_width = bar_chords_width / self.__song.get_data().get_beats_per_bar()
        i = 0
        while i < len(chords):
            if chords[i][0] == '/':
                i = i + 1
                continue
            # there is a chord on this beat
            if i % 2 == 0 \
                and i + 1 < self.__song.get_data().get_beats_per_bar() \
                and (i + 1 >= len(chords) or chords[i + 1][0] == '/' or chords[i + 1][0] == ''):
                # the next beat has no chord we can expand us
                self.__render_chord_xy(chords[i][0],
                                bar_x + (chord_width + ChordSheet.__cell_padding) * i,
                                bar_y + ChordSheet.__cell_padding,
                                chord_width + ChordSheet.__cell_padding + chord_width,
                                bar_chords_height,
                                playhead)
            else:
                self.__render_chord_xy(chords[i][0],
                                bar_x + (chord_width + ChordSheet.__cell_padding) * i,
                                bar_y + ChordSheet.__cell_padding,
                                chord_width,
                                bar_chords_height,
                                playhead)
            i = i + 1

    def __draw_repetition(self, x, y, gc, end):
        # draw line
        middle_x = x + self.__bar_info_width / 2
        start_y = y + ChordSheet.__cell_padding
        width = ChordSheet.__cell_padding
        height = ChordSheet.__bar_height - 2 * ChordSheet.__cell_padding
        self.pixmap.draw_rectangle(gc, True, middle_x, start_y, width, height)
        # draw points
        point_size = ChordSheet.__cell_padding * 2
        upper_y = y + ChordSheet.__bar_height / 4
        lower_y = y + ChordSheet.__bar_height * 3 / 4 - point_size
        if end: x = x + self.__bar_info_width / 5
        else: x = x + self.__bar_info_width * 4 / 5 - point_size
        self.pixmap.draw_arc(self.gc, True, x, upper_y, point_size, point_size, 0, 360 * 64)
        self.pixmap.draw_arc(self.gc, True, x, lower_y, point_size, point_size, 0, 360 * 64)

    def __render_bar_info_xy(self, bar_num, chord_num, bar_info, x, y, cursor, selection):
        if bar_num > self.__song.get_data().get_bar_count():
            color_code = ChordSheet.__color_no_song
        elif selection:
            color_code = ChordSheet.__color_selection
        elif cursor:
            color_code = ChordSheet.__color_cursor
        elif bar_info.has_events():
            color_code = ChordSheet.__color_events
        else:
            color_code = ChordSheet.__color_song

        color = self.__colormap.alloc_color(color_code)

        gc = self.drawable.new_gc()
        gc.copy(self.gc)
        gc.set_foreground(color)
        self.pixmap.draw_rectangle(gc, True, x , y, self.__bar_info_width, ChordSheet.__bar_height)
        if cursor: # black border
            color = self.__colormap.alloc_color('black')
            gc.set_foreground(color)
            self.pixmap.draw_rectangle(gc, False, x, y, self.__bar_info_width - 1, ChordSheet.__bar_height - 1)

        color = self.__colormap.alloc_color('black')
        gc.set_foreground(color)
        repeat_begin = bar_info.has_repeat_begin() if bar_info else False
        repeat_end = bar_info.has_repeat_end() if bar_info else False
        if repeat_begin or repeat_end: # draw repetitions
            if repeat_begin: self.__draw_repetition(x, y, gc, False)
            if repeat_end: self.__draw_repetition(x, y, gc, True)
        else:
            if bar_num < self.__song.get_data().get_bar_count() and chord_num: # draw bar number
                pango_layout = self.__area.create_pango_layout("")
                pango_layout.set_text(str(chord_num))
                fd = pango.FontDescription('Monospace Bold 8')
                pango_layout.set_font_description(fd)
                ink, logical = pango_layout.get_pixel_extents() #@UnusedVariable
                self.pixmap.draw_layout(gc, x + ChordSheet.__cell_padding,
                                    y + (ChordSheet.__bar_height - ink[1] - ink[3]) - ChordSheet.__cell_padding, pango_layout)

    def __get_pos_x(self, pos):
        return (pos / 2 % ChordSheet.__bars_per_line) * self.__bar_width \
                                        + (pos % 2 * self.__bar_info_width)

    def __get_pos_y(self, pos):
        return (pos / 2 / ChordSheet.__bars_per_line) * ChordSheet.__bar_height

    def __is_bar_info(self, field_num):
        return field_num % 2 == 0

    def __is_bar_chords(self, field_num):
        return field_num % 2 == 1

    def __render_field(self, field_num, chords=None):
        cursor = self.__cursor_pos == field_num
        playhead = self.__playhead_pos == field_num
        selection = field_num in self.__selection

        field_x = self.__get_pos_x(field_num)
        field_y = self.__get_pos_y(field_num)
        bar_num = field_num / 2

        if self.__is_bar_chords(field_num):
            if chords == None and bar_num < self.__song.get_data().get_bar_count():
                chords = self.__song.get_data().get_bar_chords(bar_num).get_chords()

            self.__render_chords_xy(bar_num, chords, field_x, field_y, playhead, cursor, selection)
            self.__area.queue_draw_area(field_x, field_y, self.__bar_chords_width, ChordSheet.__bar_height)
        else:
            bar_info = None
            if bar_num <= self.__song.get_data().get_bar_count():
                bar_info = self.__song.get_data().get_bar_info(bar_num)

            chord_num = None
            if bar_num < self.__song.get_data().get_bar_count():
                chord_num = self.__song.get_data().get_bar_chords(bar_num).get_number()

            self.__render_bar_info_xy(bar_num, chord_num, bar_info, field_x, field_y, cursor, selection)
            self.__area.queue_draw_area(field_x, field_y, self.__bar_info_width, ChordSheet.__bar_height)

    def __refresh_entries_and_events(self):
        self.__gui.refresh_bar(self.is_cursor_on_bar_chords())

    def __move_cursor_to(self, new_pos):
        old_pos = self.__cursor_pos
        self.__cursor_pos = new_pos

        self.__render_field(old_pos)

        if new_pos > self.__end_position:
            new_song_bar_count = new_pos / 2 + new_pos % 2
            self.__gui.change_song_bar_count(new_song_bar_count)

        self.__render_field(new_pos)

        self.__gui.switch_bar(self.is_cursor_on_bar_chords())
        self.__refresh_entries_and_events()

    def __redraw_selection(self, old_sel):
        removed = old_sel - self.__selection
        added = self.__selection - old_sel
        update = removed | added
        for field in update:
            self.__render_field(field)

    def __get_selection_set(self, start, end):
        if end >= start:
            return set(range(start, end + 1))
        else:
            return set(range(end, start + 1))

    def __adjust_selection(self, old_pos):
        """ Begins or adjusts field selection, redraws affected fields. """
        if self.__selection_start == None:
            # beginning a new selection
            self.__selection_start = old_pos
            self.__selection = self.__get_selection_set(old_pos, self.__cursor_pos)
            self.__redraw_selection(set([]))
        else:
            # adjust already existing selection
            old_selection = self.__selection
            self.__selection = self.__get_selection_set(self.__selection_start, self.__cursor_pos)
            self.__redraw_selection(old_selection)

    def __adjust_selection_bar_count_changed(self):
        """ Number of bars has changed, maybe destroy the selection or shorten it. """
        if self.__selection_start == None:
            return
        elif self.__selection_start > self.__end_position:
            self.__destroy_selection()
        elif max(self.__selection) > self.__end_position:
            # remove all fields from selection which are out of song
            self.__selection = set([elem for elem in self.__selection if elem <= self.__end_position])

    def __destroy_selection(self):
        if self.__selection_start == None: return
        old_selection = self.__selection
        self.__selection_start = None
        self.__selection = set([])
        self.__redraw_selection(old_selection)

    def __locate_mouse_click(self, x, y):
        bar_x = 0
        bar_chords = 0
        u = self.__bar_info_width
        while x > u:
            if bar_chords == 0:
                u = u + self.__bar_chords_width
                bar_chords = 1
            else:
                u = u + self.__bar_info_width
                bar_x = bar_x + 1
                bar_chords = 0

        bar_y = 0
        u = ChordSheet.__bar_height
        while y > u:
            u = u + ChordSheet.__bar_height
            bar_y = bar_y + 1

        pos = self.__song.get_data().get_beats_per_bar() * 2 * bar_y + bar_x * 2 + bar_chords

        return pos

