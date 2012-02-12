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
import gobject
from linuxband.glob import Glob
from linuxband.mma.bar_info import BarInfo
from linuxband.gui.common import Common


class EventGroove(object):

    __GROOVE_UNDEFINED = "Select groove"

    def __init__(self, glade, grooves):
        self.__toggled_button = None
        self.__curr_event = None
        self.__new_event = None
        self.__grooves = grooves
        self.__init_gui(glade)

    def on_treeview1_cursor_changed_callback(self, treeview):
        """ User clicked on the groove in the first column. """
        path, column = treeview.get_cursor() #@UnusedVariable
        gr = self.__groovesModel[path[0]]
        self.__treeview2.set_model(gr[6])
        self.__update_groove_info(gr)
        self.__update_groove_event(gr[0])

    def on_treeview2_cursor_changed_callback(self, treeview):
        """ User clicked on the variation of groove. """
        path, column = self.__treeview1.get_cursor() #@UnusedVariable
        model = self.__groovesModel[path[0]][6]
        path, column = self.__treeview2.get_cursor() #@UnusedVariable
        gr = model[path[0]]
        self.__update_groove_info(gr)
        self.__update_groove_event(gr[0])

    def set_label_from_event(self, button, event):
        """ Sets the label of groove button correctly
            even if the event in the self.__song.get_data().get_bar_info(0) is missing. """
        if event: button.set_label(BarInfo.get_groove_value(event))
        else: button.set_label(EventGroove.__GROOVE_UNDEFINED)

    def get_new_event(self):
        return self.__new_event

    def init_window(self, button, event):
        # hide back, forward, remove buttons
        if button is self.__togglebutton1: self.__alignment12.hide()
        else: self.__alignment12.show()
        self.__toggled_button = button
        self.__curr_event = event
        self.__new_event = None
        # if the focus stayed on the button, put it to first column
        if not self.__treeview1.is_focus() and not self.__treeview2.is_focus():
            gobject.idle_add(self.__treeview1.grab_focus)
        self.__groovesModel = self.__grooves.get_grooves_model()
        self.__treeview1.set_model(self.__groovesModel)

    def __init_gui(self, glade):
        Common.connect_signals(glade, self)
        # back, forward, remove event buttons will be hidden
        self.__alignment12 = glade.get_widget("alignment12")
        # groove description
        groove_window = glade.get_widget("grooveWindow")
        textview2 = glade.get_widget("textview2")
        self.__textbuffer2 = textview2.get_buffer()
        # text colors      
        colormap = groove_window.get_colormap()
        color = colormap.alloc_color('red')
        self.__textbuffer2.create_tag('fg_red', foreground_gdk=color)
        color = colormap.alloc_color('brown');
        self.__textbuffer2.create_tag('fg_brown', foreground_gdk=color)
        color = colormap.alloc_color('black');
        self.__textbuffer2.create_tag('fg_black', foreground_gdk=color)
        self.__textbuffer2.create_tag("bold", weight=pango.WEIGHT_BOLD)
        self.__togglebutton1 = glade.get_widget("togglebutton1")
        # groove columns
        self.__treeview1 = glade.get_widget("treeview1")
        self.__treeview2 = glade.get_widget("treeview2")
        # grooves column
        tvcolumn = gtk.TreeViewColumn('Groove')
        self.__treeview1.append_column(tvcolumn)
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.set_attributes(cell, text=0)
        # groove variation column
        self.__treeview2.set_model(None)
        tvcolumn = gtk.TreeViewColumn('Variation')
        self.__treeview2.append_column(tvcolumn)
        cell = gtk.CellRendererText()
        tvcolumn.pack_start(cell, True)
        tvcolumn.set_attributes(cell, text=0)

    def __update_groove_info(self, gr):
        """ Update description, author ... of the currently selected groove. """
        tb = self.__textbuffer2
        tb.set_text('')
        start, end = tb.get_bounds() #@UnusedVariable
        tb.insert_with_tags_by_name(end, gr[0] + '\n', 'fg_brown', 'bold')
        tb.insert(end, gr[1] + '\n\n')
        tb.insert_with_tags_by_name(end, gr[2] + '\n\n', 'bold')
        tb.insert_with_tags_by_name(end, 'Author' + '\n', 'fg_brown')
        tb.insert(end, gr[3] + '\n\n')
        tb.insert_with_tags_by_name(end, 'File' + '\n', 'fg_brown')
        tb.insert(end, gr[5] + '\n\n')

    def __update_groove_event(self, groove):
        event = BarInfo.create_event(Glob.A_GROOVE)
        BarInfo.set_groove_value(event, groove)
        self.set_label_from_event(self.__toggled_button, event)
        self.__new_event = event
