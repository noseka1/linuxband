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

import pango
import logging
import gtk.glade
import gobject
from linuxband.glob import Glob
from linuxband.gui.gui_logger import GuiLogger
from linuxband.config import Config
from linuxband.midi.midi_player import MidiPlayer
from linuxband.gui.chord_sheet import ChordSheet
from linuxband.gui.source_editor import SourceEditor
from linuxband.gui.chord_entries import ChordEntries
from linuxband.gui.events_bar import EventsBar
from linuxband.gui.common import Common
from linuxband.mma.song import Song
from linuxband.mma.grooves import Grooves
from linuxband.gui.about_dialog import AboutDialog
from linuxband.midi.mma2smf import MidiGenerator
from linuxband.gui.preferences import Preferences
from linuxband.gui.save_button_status import SaveButtonStatus


class Gui:

    def application_end_event_callback(self, *args):
        self.__do_application_end()
        return True

    def switch_bar(self, on_bar_chords):
        """
        If we are not on chords field hide the chord entries and show events.
        """
        if on_bar_chords:
            self.__chord_entries.show()
            self.__events_bar.hide()
        else:
            self.__events_bar.show()
            self.__chord_entries.hide()

    def refresh_bar(self, on_bar_chords):
        """ Refresh chord_entries or events_bar. """
        if on_bar_chords:
            self.__chord_entries.refresh()
        else:
            self.__events_bar.refresh_all()

    def refresh_current_field(self):
        self.__chord_sheet.render_current_field()

    def refresh_chord_sheet(self):
        self.__set_song_bar_count(self.__song.get_data().get_bar_count())

    def is_cursor_on_bar_chords(self):
        return self.__chord_sheet.is_cursor_on_bar_chords()

    def get_current_bar_number(self):
        return self.__chord_sheet.get_current_bar_number()

    def move_playhead_to_bar(self, barNum):
        """ Called by MidiPlayer. """
        self.__chord_sheet.move_playhead_to(barNum)

    def move_playhead_to_line(self, lineNum):
        """ Called by MidiPlayer. """
        self.__source_editor.move_playhead_to(lineNum)

    def hide_playhead(self):
        self.__chord_sheet.move_playhead_to(-1)
        self.__source_editor.move_playhead_to(-1)

    def main_window_keypress_event_callback(self, widget, event):
        key = event.keyval
        keyname = gtk.gdk.keyval_name(key)
        # print 'KEY %s %s' % (key, keyname)
        if keyname in '12345678':
            if self.__chord_sheet.has_focus() and self.__chord_sheet.is_cursor_on_bar_chords():
                if int(keyname) <= self.__song.get_data().get_beats_per_bar():
                    self.__chord_entries.grab_focus(int(keyname) - 1)
                return True
        elif keyname in 'CDEFGAB':
            if self.__chord_sheet.has_focus() and self.__chord_sheet.is_cursor_on_bar_chords():
                self.__chord_entries.begin_writing(keyname)
                return True
        elif keyname == 'e' and self.__chord_sheet.has_focus(): # TODO: doesn't work
            self.__events_bar.grab_focus()
            return True
        elif (self.__chord_sheet.has_focus() or self.__notebook3.has_focus()) and keyname == 'space':
            if (self.__midi_player.is_playing()):
                self.playback_stop_callback()
            else:
                self.playback_start(None, event)
            return True
        # propagate the event further
        return False

    def edit_cut_callback(self, menuitem):
        if self.__chord_sheet.has_focus():
            self.__chord_sheet.cut_selection()
        elif self.__source_editor.has_focus():
            self.__source_editor.cut_selection()
        elif self.__chord_entries.has_focus():
            self.__chord_entries.cut_selection()

    def edit_copy_callback(self, menuitem):
        if self.__chord_sheet.has_focus():
            self.__chord_sheet.copy_selection()
        elif self.__source_editor.has_focus():
            self.__source_editor.copy_selection()
        elif self.__chord_entries.has_focus():
            self.__chord_entries.copy_selection()

    def edit_paste_callback(self, menuitem):
        if self.__chord_sheet.has_focus():
            self.__chord_sheet.paste_selection()
        elif self.__source_editor.has_focus():
            self.__source_editor.paste_selection()
        elif self.__chord_entries.has_focus():
            self.__chord_entries.paste_selection()

    def edit_delete_callback(self, menuitem):
        if self.__chord_sheet.has_focus():
            self.__chord_sheet.delete_selection()
        elif self.__source_editor.has_focus():
            self.__source_editor.delete_selection()
        elif self.__chord_entries.has_focus():
            self.__chord_entries.delete_selection()

    def edit_select_all_callback(self, menuitem):
        if self.__chord_sheet.has_focus():
            self.__chord_sheet.select_all()
        elif self.__source_editor.has_focus():
            self.__source_editor.select_all()
        elif self.__chord_entries.has_focus():
            self.__chord_entries.select_all()

    def view_preferences_callback(self, menuitem):
        """ Preferences. """
        self.__preferences.run()

    __ignore_toggle2 = False
    def switch_view_callback(self, item=None):
        if Gui.__ignore_toggle2:
            Gui.__ignore_toggle2 = False
        else:
            if self.__menuitem5.get_active():
                self.__notebook3.set_current_page(0)
            else:
                self.__notebook3.set_current_page(1)

    def spinbutton_keyrelease_event_callback(self, widget, event):
        """ For songBarCount and introLength spin buttons """
        key = event.keyval
        if key == gtk.keysyms.Return or key == gtk.keysyms.KP_Enter or key == gtk.keysyms.Escape:
            self.__chord_sheet.grab_focus()
        return True

    def song_bar_count_value_changed_callback(self, widget):
        self.change_song_bar_count(widget.get_value_as_int())

    def intro_length_value_changed_callback(self, widget):
        length = widget.get_value_as_int()
        self.__midi_player.set_intro_length(length)
        self.__config.set_intro_length(length)

    def chord_sheet_button_press_event_callback(self, widget, event):
        self.__events_bar.toggle_window_cancel_callback(None)
        self.__chord_sheet.drawing_area_clicked(widget, event)
        return False

    def change_song_bar_count(self, bar_count):
        """
        Set the count of song bars to bar_count.
        
        Redraw affected fields
        Move cursor if it is necessary
        """
        self.__spinbutton1.set_text(str(bar_count))
        self.__song.get_data().change_bar_count(bar_count)
        self.__chord_sheet.change_song_bar_count(bar_count)

    def song_title_keyrelease_event_callback(self, widget, event):
        """ Finish Song title editing. """
        key = event.keyval
        if key == gtk.keysyms.Return or key == gtk.keysyms.KP_Enter:
            self.__song.get_data().set_title(widget.get_text())
            self.__chord_sheet.grab_focus()
        return True

    def new_file_callback(self, menuitem):
        """ New. """
        if self.__handle_unsaved_changes():
            self.__do_new_file()

    def open_file_callback(self, menutime):
        """ Open. """
        if self.__handle_unsaved_changes():
            if (self.__open_file_dialog.get_current_folder() <> self.__config.get_work_dir()):
                self.__open_file_dialog.set_current_folder(self.__config.get_work_dir())
            result = self.__open_file_dialog.run()
            self.__open_file_dialog.hide()
            if (result == gtk.RESPONSE_OK):
                self.__config.set_work_dir(self.__open_file_dialog.get_current_folder())
                full_name = self.__open_file_dialog.get_filename()
                manager = gtk.recent_manager_get_default()
                manager.add_item('file://' + full_name)
                self.__input_file = full_name
                self.__output_file = full_name
                self.__do_open_file()

    def open_recent_file(self, widget):
        if self.__handle_unsaved_changes():
            uri = widget.get_current_item().get_uri()
            file_name = uri[7:]
            manager = gtk.recent_manager_get_default()
            manager.add_item('file://' + file_name)
            self.__input_file = file_name
            self.__output_file = file_name
            self.__do_open_file()

    def save_file_callback(self, menuitem):
        """ Save. """
        self.__do_save_file()

    def save_file_as_callback(self, menuitem):
        """ Save as. """
        self.__do_save_as()

    def export_midi_callback(self, menuitem):
        """ Export MIDI. """
        if self.__compile_song(True) == 0:
            if (self.__export_midi_dialog.get_current_folder() <> self.__config.get_work_dir()):
                self.__export_midi_dialog.set_current_folder(self.__config.get_work_dir())
            out_file = self.__output_file if self.__output_file else Glob.OUTPUT_FILE_DEFAULT
            out_file = self.__change_extension(out_file, "mid")
            logging.debug(out_file)
            self.__export_midi_dialog.set_current_name(out_file)
            result = self.__export_midi_dialog.run()
            self.__export_midi_dialog.hide()
            if (result == gtk.RESPONSE_OK):
                self.__config.set_work_dir(self.__export_midi_dialog.get_current_folder())
                full_name = self.__export_midi_dialog.get_filename()
                self.__song.write_to_midi_file(full_name)
        else:
            logging.error("Failed to compile MMA file. Fix the errors and try the export again.")

    def playback_start(self, button, event):
        """ Play. """
        if event.state & gtk.gdk.SHIFT_MASK and event.state & gtk.gdk.CONTROL_MASK:
            self.__compile_song(True)
        else:
            player = self.__midi_player
            res = self.__compile_song(True)
            if res == 0:
                res, midi_data = self.__song.get_playback_midi_data()
                player.playback_stop()
                if res != 0: # generate SMF failed
                    if res > 0 or res == -1: self.__show_mma_error(res)
                    return
                player.load_smf_data(midi_data, self.__song.get_data().get_mma_line_offset())
            else:
                return
            self.__enable_pause_button();
            if event.state & gtk.gdk.CONTROL_MASK:
                player.playback_start_bar(self.__chord_sheet.get_current_bar_number())
            elif event.state & gtk.gdk.SHIFT_MASK:
                player.playback_start_bars(self.__chord_sheet.get_selection_limits())
            else:
                player.playback_start()

    def playback_stop_callback(self, button=None):
        """ Stop. """
        self.__enable_pause_button();
        self.__midi_player.playback_stop()

    __ignore_toggle = False
    def playback_pause_callback(self, button=None):
        """ Pause. """
        if Gui.__ignore_toggle:
            Gui.__ignore_toggle = False
        else:
            self.__midi_player.set_pause(button.get_active());

    def jack_reconnect_callback(self, button):
        self.__midi_player.shutdown()
        self.__midi_player.startup();

    def switch_page_callback(self, notebook, page, pageNum):
        """ Called when clicked on notebook tab. """
        logging.debug("")
        if pageNum == 1: # switching to source editor
            self.__source_editor.refresh_source(self.__song.write_to_string())
            self.__source_editor.grab_focus()
            self.__notebook2.set_current_page(pageNum)
            # view menu item
            if not self.__menuitem7.get_active():
                Gui.__ignore_toggle2 = True
                self.__menuitem7.set_active(True)
            self.__global_buttons.hide()
        else: # switching to chord sheet
            res = self.__compile_song(True)
            if res > 0 or res == -1:
                logging.error("Cannot switch to chord sheet view. Fix the errors and try again.")
            else:
                self.refresh_chord_sheet()
                self.__refresh_song_title()
                self.__events_bar.refresh_all()
                self.__notebook2.set_current_page(pageNum)
                # view menu item
                if not self.__menuitem5.get_active():
                    Gui.__ignore_toggle2 = True
                    self.__menuitem5.set_active(True)
                self.__global_buttons.show()

    def loop_toggle_callback(self, button):
        """ Loop check button. """
        self.__midi_player.set_loop(button.get_active());
        self.__config.set_loop(button.get_active())

    def jack_transport_toggle_callback(self, button):
        """ Use JACK transport check button. """
        self.__midi_player.use_jack_transport(button.get_active())
        self.__config.set_jack_transport(button.get_active())

    def __enable_pause_button(self):
        if self.__toolbutton3.get_active():
            Gui.__ignore_toggle = True
            self.__toolbutton3.set_active(False)

    def __do_application_end(self):
        if self.__handle_unsaved_changes():
            # stop the jack thread when exiting
            if self.__midi_player:
                self.__midi_player.shutdown()
            self.__config.save_config()
            gtk.main_quit()

    def __set_song_bar_count(self, bar_count):
        self.__spinbutton1.set_text(str(bar_count))
        self.__chord_sheet.set_song_bar_count(bar_count)

    def __refresh_song_title(self):
        self.__entry9.set_text(self.__song.get_data().get_title())

    def __do_new_file(self):
        self.__output_file = None
        self.__input_file = self.__config.getTemplateFile()
        self.__do_open_file()

    def __do_open_file(self):
        self.playback_stop_callback()
        self.__song.load_from_file(self.__input_file)
        res = self.__song.compile_song()
        self.__chord_sheet.new_song_loaded()
        self.__source_editor.new_song_loaded(self.__song.write_to_string())
        self.refresh_chord_sheet()
        self.__refresh_song_title()
        if res > 0 or res == -1: self.__show_mma_error(res)

    def __do_save_as(self):
        if (self.__save_as_dialog.get_current_folder() <> self.__config.get_work_dir()):
            self.__save_as_dialog.set_current_folder(self.__config.get_work_dir())
        self.__save_as_dialog.set_current_name(Glob.OUTPUT_FILE_DEFAULT)
        result = self.__save_as_dialog.run()
        self.__save_as_dialog.hide()
        if (result == gtk.RESPONSE_OK):
            self.__config.set_work_dir(self.__save_as_dialog.get_current_folder())
            full_name = self.__save_as_dialog.get_filename()
            self.__compile_song(False)
            self.__song.write_to_mma_file(full_name)
            self.__output_file = full_name
            return True
        else:
            return False

    def __do_save_file(self):
        if self.__output_file == None:
            return self.__do_save_as()
        else:
            self.__compile_song(False)
            self.__song.write_to_mma_file(self.__output_file)
            return True

    def __handle_unsaved_changes(self):
        if self.__song.get_data().is_save_needed():
            self.__save_changes_dialog.set_property("text", "Save changes to " + self.__song.get_data().get_title() + "?")
            self.__save_changes_dialog.set_property("secondary_text", "Your changes will be lost if you don't save them.")
            result = self.__save_changes_dialog.run()
            self.__save_changes_dialog.hide()
            if (result == gtk.RESPONSE_YES):
                return self.__do_save_file()
        return True

    def __change_extension(self, file_name, ext):
        name_and_extension = file_name.rsplit('.', 1)
        if len(name_and_extension) == 2:
            return ''.join([name_and_extension[0], '.', ext])
        else:
            return file_name

    def __compile_song(self, show_error):
        logging.debug("COMPILE_SONG")
        res = self.__song.compile_song()
        if show_error:
            if res == 0:
                self.__source_editor.put_error_mark_to(-1)
            elif res > 0 or res == -1:
                self.__show_mma_error(res)
        return res

    def __show_mma_error(self, lineNum):
        self.__source_editor.put_error_mark_to(lineNum - 1)
        self.__notebook2.set_current_page(1)
        gobject.idle_add(self.__notebook3.set_current_page, 1)
        self.__source_editor.grab_focus()

    def __init_recent_menu(self, glade):
        # code here comes from http://lescannoniers.blogspot.com/2008/11/pygtk-recent-file-chooser.html
        # add a recent files menu item
        manager = gtk.recent_manager_get_default()
        # define a RecentChooserMenu object 
        recent_menu_chooser = gtk.RecentChooserMenu(manager)
        # define a file filter, otherwise all file types will show up
        file_filter = gtk.RecentFilter()
        file_filter.add_pattern("*.mma")
        # add the file_filter to the RecentChooserMenu object
        recent_menu_chooser.add_filter(file_filter)
        recent_menu_chooser.set_sort_type(gtk.RECENT_SORT_MRU)
        recent_menu_chooser.set_limit(10)
        recent_menu_chooser.set_show_tips(True)
        recent_menu_chooser.set_show_numbers(True)
        recent_menu_chooser.set_local_only(True)
        # add a signal to open the selected file
        recent_menu_chooser.connect("item-activated", self.open_recent_file)
        # attach the RecentChooserMenu to the main menu item
        menuitem6 = glade.get_widget("menuitem6")
        menuitem6.set_submenu(recent_menu_chooser)
        # attach the RecentChooserMenu to the Open tool button
        toolbutton8 = glade.get_widget("toolbutton8")
        toolbutton8.set_menu(recent_menu_chooser)

    def __init_filechooser_dialogs(self, glade):
        self.__open_file_dialog = glade.get_widget("openFileDialog")
        self.__save_as_dialog = glade.get_widget("saveAsDialog")
        self.__export_midi_dialog = glade.get_widget("exportMidiDialog")
        # set file filters for Open and Save as dialogs
        filter1 = gtk.FileFilter()
        filter1.set_name("MMA files")
        filter1.add_pattern("*.mma")
        filter2 = gtk.FileFilter()
        filter2.set_name("All files")
        filter2.add_pattern("*")
        filter3 = gtk.FileFilter()
        filter3.set_name("MIDI files")
        filter3.add_pattern("*.mid")
        self.__open_file_dialog.add_filter(filter1)
        self.__open_file_dialog.add_filter(filter2)
        self.__save_as_dialog.add_filter(filter1)
        self.__save_as_dialog.add_filter(filter2)
        self.__export_midi_dialog.add_filter(filter2)
        self.__export_midi_dialog.add_filter(filter3)

    def __init__(self):
        glade = gtk.glade.XML(Glob.GLADE)
        GuiLogger.initLogging(glade)
        Common.connect_signals(glade, self)

        self.__main_window = glade.get_widget("mainWindow")
        self.__spinbutton1 = glade.get_widget("spinbutton1") # bar count 
        self.__notebook2 = glade.get_widget("notebook2")
        self.__notebook3 = glade.get_widget("notebook3")

        # song name
        self.__entry9 = glade.get_widget("entry9")
        self.__entry9.modify_font(pango.FontDescription('10'))

        # global buttons
        self.__global_buttons = glade.get_widget("vbox10")

        # pause button
        self.__toolbutton3 = glade.get_widget("toolbutton3")

        # view menu toggle
        self.__menuitem5 = glade.get_widget("menuitem5")
        self.__menuitem7 = glade.get_widget("menuitem7")

        # hack to get event object when clicked on toolbutton
        toolbutton1 = glade.get_widget("toolbutton1")
        toolbutton1.get_children()[0].connect('button-press-event', self.playback_start)

        # save changes dialog
        self.__save_changes_dialog = glade.get_widget("saveChangesDialog")

        self.__config = Config()
        self.__config.load_config()
        grooves = Grooves(self.__config)
        grooves.load_grooves(True)

        self.__song = song = Song(MidiGenerator(self.__config))
        self.__chord_sheet = ChordSheet(glade, song, self, self.__config)
        self.__events_bar = EventsBar(glade, song, self, grooves)
        self.__chord_entries = ChordEntries(glade, song, self.__chord_sheet)
        self.__source_editor = SourceEditor(glade, song)
        self.__preferences = Preferences(glade, self, self.__config, grooves)

        AboutDialog(glade)
        SaveButtonStatus(glade, song)

        self.__init_recent_menu(glade)
        self.__init_filechooser_dialogs(glade)

        self.__main_window .show()

        gobject.threads_init()
        self.__midi_player = MidiPlayer(self)
        if (self.__config.get_jack_connect_startup()):
            self.__midi_player.startup()

        # loop check button, must be after the __midiPlayer.startup() call
        checkbutton1 = glade.get_widget("checkbutton1")
        checkbutton1.set_active(self.__config.get_loop())

        # jack transport check button, must be after the __midiPlayer.startup() call
        checkbutton3 = glade.get_widget("checkbutton3")
        checkbutton3.set_active(self.__config.get_jack_transport())

        # intro length, , must be after the __midiPlayer.startup() call
        spinbutton3 = glade.get_widget("spinbutton3")
        spinbutton3.set_value(self.__config.get_intro_length())

        self.__do_new_file()
        gtk.main()

