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
import gobject
from gtk.gdk import CONTROL_MASK
from linuxband.gui.common import Common
from linuxband.mma.chord_table import chordlist


class ChordEntries(object):

    def __init__(self, glade, song, chord_sheet):
        self.__song = song
        self.__completion_match = False
        self.__init_gui(glade, self.__get_chord_names())
        self.__chord_sheet = chord_sheet

    def refresh(self):
        """ Refresh chord entries. """
        if self.__chord_sheet.is_cursor_on_bar_info(): return
        barnum = self.__chord_sheet.get_current_bar_number()

        for entry in self.__entries:
            entry.set_text('')

        if barnum < self.__song.get_data().get_bar_count():
            chords = self.__song.get_data().get_bar_chords(barnum).get_chords()
            for i in range(len(chords)):
                chord = chords[i][0]
                if chord == '/': # don't show '/' as chord
                    self.__entries[i].set_text('')
                else:
                    self.__entries[i].set_text(chord)
        else:
            for i in range(self.__song.get_data().get_beats_per_bar()):
                self.__entries[i].set_text('')

    def on_entry_key_release_event_callback(self, widget, event):
        key = event.keyval
        if key == gtk.keysyms.Escape \
            or (event.state & CONTROL_MASK and key == gtk.keysyms.bracketright):
            # cancel chord editing
            self.__chord_sheet.render_current_field()
            self.refresh()
            self.__chord_sheet.grab_focus()
            return False
        chords = []
        for i in range(self.__song.get_data().get_beats_per_bar()):
            chords.append([self.__entries[i].get_text()])
        self.__chord_sheet.render_current_field(chords)
        if key == gtk.keysyms.Return or key == gtk.keysyms.KP_Enter:
            if self.__completion_match:
                self.__completion_match = False
            else:
                self.__chord_sheet.chord_entry_editing_finished()
        return False

    def on_entry_focus_out_event_callback(self, widget, event):
        """ Set the chord. """
        barnum = self.__chord_sheet.get_current_bar_number()
        beatnum = self.__entries.index(widget)
        chord = widget.get_text()
        self.__song.get_data().get_bar_chords(barnum).set_chord(beatnum, chord)
        return False

    def begin_writing(self, char):
        """ Called from ChordSheet when any of CDEFGAB has been pressed. """
        self.__entries[0].set_text(char)
        self.__entries[0].grab_focus()
        self.__entries[0].get_completion().complete()
        self.__entries[0].select_region(-1, -1)

    def grab_focus(self, num):
        gobject.idle_add(self.__entries[num].grab_focus)

    def has_focus(self):
        return self.__find_focused_entry() != None

    def hide(self):
        self.__hbox6.hide()

    def show(self):
        self.__hbox6.show()

    def cut_selection(self):
        entry = self.__find_focused_entry()
        entry.cut_clipboard()

    def copy_selection(self):
        entry = self.__find_focused_entry()
        entry.copy_clipboard()

    def paste_selection(self):
        entry = self.__find_focused_entry()
        entry.paste_clipboard()

    def delete_selection(self):
        entry = self.__find_focused_entry()
        entry.delete_selection()

    def select_all(self):
        entry = self.__find_focused_entry()
        entry.select_region(0, -1)

    def __init_gui(self, glade, chord_names):
        Common.connect_signals(glade, self)
        self.__hbox6 = glade.get_widget("hbox6")
        self.__entries = [ glade.get_widget("entry1"),
                         glade.get_widget("entry2"),
                         glade.get_widget("entry3"),
                         glade.get_widget("entry4"),
                         glade.get_widget("entry5"),
                         glade.get_widget("entry6"),
                         glade.get_widget("entry7"),
                         glade.get_widget("entry8") ]
        # Initialize chord entry completion
        model = gtk.ListStore(str)
        for chord in chord_names:
            model.append([chord])
        for entry in self.__entries:
            completion = gtk.EntryCompletion()
            completion.set_model(model)
            completion.set_text_column(0)
            completion.set_match_func(self.__match_function)
            completion.connect("match-selected", self.__on_completion_match)
            entry.set_completion(completion)
        # hide redundant entries
        for entry in self.__entries[self.__song.get_data().get_beats_per_bar():]:
            entry.hide()
        # create a focus cycle
        focus_chain = []
        for entry in self.__entries[:self.__song.get_data().get_beats_per_bar()]:
            focus_chain.append(entry)
        focus_chain.append(self.__entries[0])
        self.__hbox6.set_focus_chain(focus_chain)

    def __get_chord_names(self):
        """
        Generate a list with all possible chords.
        
        It is used for entry completion
        """
        base = [ 'C', 'D', 'E', 'F', 'G', 'A', 'B' ]
        base_ext = []
        for c in base:
            base_ext.append(c)
            base_ext.append(c + '#')
            base_ext.append(c + 'b')

        chord_names = []
        for c in base_ext:
            for k, v in chordlist.iteritems(): #@UnusedVariable
                chord_names.append(c + k)

        chord_names.sort()
        return chord_names

    def __match_function(self, completion, key, it):
        # key is case-insensitive
        model = completion.get_model()
        key = completion.get_entry().get_text()
        return model[it][0].startswith(key)

    def __on_completion_match(self, completion, model, it):
        self.__completion_match = True

    def __find_focused_entry(self):
        for entry in self.__entries:
            if entry.is_focus():
                return entry
        return None
