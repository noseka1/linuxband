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
from linuxband.glob import Glob
from linuxband.gui.common import Common
from linuxband.gui.events.groove import EventGroove
from linuxband.gui.events.repeat import EventRepeat
from linuxband.gui.events.repeat_end import EventRepeatEnd
from linuxband.gui.events.repeat_ending import EventRepeatEnding
from linuxband.gui.events.tempo import EventTempo
from linuxband.mma.bar_info import BarInfo


class EventsBar(object):

    def __init__(self, glade, song, gui, grooves):
        self.__song = song
        # triple = [ button, window, handler, event ]
        self.__triples = []
        # triple which window is currently active
        self.__toggled_triple = None
        # toggleWindowClose workaround
        self.__toggle_window_close_recursive = False
        # original label on toggle button just before opening the window
        self.__toggled_button_label = None
        # event which is being edited in the toggleWindow    
        self.__curr_event = None
        self.__grooves = grooves
        self.__gui = gui
        self.__init_gui(glade)

    def move_event_backwards_callback(self, widget):
        """ Move events button and it's window to the left. """
        box = self.__hbox8
        index = box.child_get_property(self.__toggled_triple[0], "position")
        if index > 0:
            # move event in the model
            barNum = self.__gui.get_current_bar_number()
            self.__song.get_data().get_bar_info(barNum).move_event_backwards(self.__curr_event)
            # move the button and its window
            box.reorder_child(self.__toggled_triple[0], index - 1)
            gobject.idle_add(self.__move_window_underneath, self.__toggled_triple[1], self.__toggled_triple[0])
            # we could have moved the tempo event to the beginning -> became the global tempo
            self.__refresh_globals()

    def move_event_forwards_callback(self, widget):
        """ Move events button and it's window to the right. """
        box = self.__hbox8
        index = box.child_get_property(self.__toggled_triple[0], "position")
        if index < len(box.get_children()) - 1:
            # move event in the model
            barNum = self.__gui.get_current_bar_number()
            self.__song.get_data().get_bar_info(barNum).move_event_forwards(self.__curr_event)
            # move the button and its window
            box.reorder_child(self.__toggled_triple[0], index + 1)
            gobject.idle_add(self.__move_window_underneath, self.__toggled_triple[1], self.__toggled_triple[0])
            # the global tempo or the global groove could have been changed
            self.__refresh_globals()

    def remove_event_callback(self, widget):
        """ Remove the event from event bar. """
        # remove event from the model
        barNum = self.__gui.get_current_bar_number()
        self.__song.get_data().get_bar_info(barNum).remove_event(self.__curr_event)
        # remove the window from the triples list
        self.__remove_from_triples(self.__toggled_triple[0])
        # remove button and close the window
        self.__hbox8.remove(self.__toggled_triple[0])
        self.__toggle_window_close() # deletes the self.__toggled_triple
        self.__refresh_globals()
        self.__gui.refresh_current_field() # repetition

    def add_event_clicked_callback(self, button):
        """ Add event button pressed. """
        menu = self.__addEventMenu
        x, y = self.__get_widget_xy_position(button, menu)
        self.__toggle_window_close()
        event = gtk.get_current_event()
        menu.popup(None, None, lambda menu: (x, y, True), event.button, event.time)

    def toggle_button_clicked_callback(self, button, event=None):
        """ User clicked on toggle button (global button or event button). """
        if button.get_active():
            # button is pressed in
            if self.__toggled_triple:
                # some other button is toggled
                self.__toggle_window_close()
            for triple in self.__triples:
                if triple[0] is button: break
            self.__toggled_button_label = button.get_label()
            if button is self.__togglebutton1:
                self.__curr_event = self.__song.get_data().get_bar_info(0).get_groove()
            elif button is self.__togglebutton2:
                self.__curr_event = self.__song.get_data().get_bar_info(0).get_tempo()
            else:
                self.__curr_event = event
            self.__move_window_underneath(triple[1], button)
            triple[2].init_window(button, self.__curr_event)
            triple[1].show()
            self.__toggled_triple = triple
        else:
            # button is released
            self.__toggle_window_close()

    def toggle_window_expose_event_callback(self, widget, event):
        self.__draw_window_border(widget)
        return False

    def toggle_window_cancel_callback(self, widget):
        """ Toggle window cancel button clicked. """
        self.__toggle_window_close(True)

    def toggle_window_ok_callback(self, widget, *args):
        """ Toggle window OK button clicked. """
        # we didn't touch the settings, don't set label
        newEvent = self.__toggled_triple[2].get_new_event()
        button = self.__toggled_triple[0]
        if not newEvent:
            self.__toggle_window_close(True)
        else:
            self.__toggle_window_close(False)
            if button in [self.__togglebutton1, self.__togglebutton2]:
                if not self.__curr_event: self.__song.get_data().get_bar_info(0).add_event(newEvent)
                else: self.__song.get_data().get_bar_info(0).replace_event(self.__curr_event, newEvent)
            else:
                barNum = self.__gui.get_current_bar_number()
                self.__song.get_data().get_bar_info(barNum).replace_event(self.__curr_event, newEvent)
            self.refresh_all() # global groove or global tempo could have been changed

    def main_window_configure_event_callback(self, widget, event):
        """ Everytime the main window is moved or resised, move the toggle window with it. """
        if self.__toggled_triple:
            self.__move_window_underneath(self.__toggled_triple[1], self.__toggled_triple[0])
        return False

    def toggle_window_key_pressed_event_callback(self, widget, event):
        """ If the Escape was pressed, close the toggle window. """
        key = event.keyval
        if key == gtk.keysyms.Escape:
            self.__toggle_window_close(True)
            return True

    def refresh_all(self):
        """ Refresh global buttons Select groove, Select tempo and event buttons. """
        self.__refresh_globals()
        self.__refresh_events_bar()

    def grab_focus(self):
        """ First event button or Add event button takes focus. """
        if len(self.__triples) > 0:
            self.__triples[0][0].grab_focus()
        else:
            self.__button17.grab_focus()

    def hide(self):
        self.__hbox7.hide()

    def show(self):
        self.__hbox7.show()

    def __init_gui(self, glade):
        Common.connect_signals(glade, self)
        self.__main_window = glade.get_widget("mainWindow")
        groove_window = glade.get_widget("grooveWindow")
        tempo_window = glade.get_widget("tempoWindow")
        repeat_window = glade.get_widget("repeatWindow")
        repeat_end_window = glade.get_widget("repeatEndWindow")
        repeat_ending_window = glade.get_widget("repeatEndingWindow")
        self.__hbox8 = glade.get_widget("hbox8")
        self.__hbox7 = glade.get_widget("hbox7")
        # add event button
        self.__button17 = glade.get_widget("button17")
        # global groove and tempo buttons
        self.__togglebutton1 = glade.get_widget("togglebutton1")
        self.__togglebutton2 = glade.get_widget("togglebutton2")
        # global buttons
        self.__eventGroove = EventGroove(glade, self.__grooves)
        self.__eventTempo = EventTempo(glade)
        self.__triples.append([ self.__togglebutton1, groove_window, self.__eventGroove, None ])
        self.__triples.append([ self.__togglebutton2, tempo_window, self.__eventTempo, None ])
        # add event menu
        event_items = { Glob.A_GROOVE: "Groove change",
                      Glob.A_TEMPO: "Tempo change",
                      Glob.A_REPEAT: "Repeat",
                      Glob.A_REPEAT_ENDING: "RepeatEnding",
                      Glob.A_REPEAT_END: "RepeatEnd" }
        self.__addEventMenu = gtk.Menu()
        menu = self.__addEventMenu
        for key in Glob.EVENTS:
            item = gtk.MenuItem(event_items[key])
            item.connect_object("activate", self.__add_event, key)
            menu.append(item)
        menu.show_all()
        # for dynamic event creation
        self.__event_windows = { Glob.A_GROOVE: groove_window,
                              Glob.A_TEMPO: tempo_window,
                              Glob.A_REPEAT: repeat_window,
                              Glob.A_REPEAT_ENDING: repeat_ending_window,
                              Glob.A_REPEAT_END: repeat_end_window }

        self.__event_window_handlers = { Glob.A_GROOVE: self.__eventGroove, # reusing already existing object
                                      Glob.A_TEMPO: self.__eventTempo,
                                      Glob.A_REPEAT: EventRepeat(glade),
                                      Glob.A_REPEAT_ENDING: EventRepeatEnding(glade),
                                      Glob.A_REPEAT_END: EventRepeatEnd(glade) }

    def __refresh_events_bar(self):
        """ Refresh events bar """
        if self.__gui.is_cursor_on_bar_chords(): return
        barNum = self.__gui.get_current_bar_number()
        box = self.__hbox8
        children = box.get_children()
        # remove widgets from triples and events bar
        for child in children:
            self.__remove_from_triples(child)
            box.remove(child)
        # recreate event buttons
        events = self.__song.get_data().get_bar_info(barNum).get_events()
        for event in events:
            title = event[0]
            button = gtk.ToggleButton()
            window = self.__event_windows[title]
            handler = self.__event_window_handlers[title]
            self.__triples.append([button, window, handler, event])
            handler.set_label_from_event(button, event)
            button.connect("clicked", self.toggle_button_clicked_callback, event)
            box.pack_start(button, False, False, 0)
            button.show()

    def __add_event(self, key):
        """ Add selected event and open its window """
        barNum = self.__gui.get_current_bar_number()
        event = BarInfo.create_event(key)
        self.__song.get_data().get_bar_info(barNum).add_event(event)
        self.refresh_all()
        self.__gui.refresh_current_field() # repetition
        # open the new event window
        for triple in self.__triples:
            if triple[3] is event:
                gobject.idle_add(triple[0].clicked)
                break

    def __remove_from_triples(self, button):
        for triple in self.__triples:
            if triple[0] is button: break
        if triple[0] is button:
            self.__triples.remove(triple)

    def __move_window_underneath(self, gtkwindow, widget):
        """ Move window to appear directly under the toggled button """
        rect = widget.get_allocation()
        rect2 = self.__main_window.get_allocation() # (0, 0, 1100, 700)

        # black magic to get the correct values into rect3 
        gtkwindow.realize()
        gtkwindow.window.get_root_origin()

        rect3 = gtkwindow.get_allocation()

        # this has a side effect that x, y on the following line are set properly
        x1, y1 = self.__main_window.window.get_root_origin() # decoration window  @UnusedVariable
        x, y = self.__main_window.window.get_origin() # our window

        wx = min(x + rect.x, x + rect2.width - rect3.width)
        wy = y + rect.y + rect.height

        gtkwindow.move(wx, wy)

    def __get_widget_xy_position(self, widget, gtkwindow):
        #""" Move window to appear directly under the toggle button """
        rect = widget.get_allocation()
        rect2 = self.__main_window.get_allocation() # (0, 0, 1100, 700)

        # black magic to get the correct values into rect3 
        gtkwindow.realize()
        gtkwindow.window.get_root_origin()

        rect3 = gtkwindow.get_allocation()

        # this has a side effect that x, y on the following line are set properly
        x1, y1 = self.__main_window.window.get_root_origin() # decoration window  @UnusedVariable
        x, y = self.__main_window.window.get_origin() # our window

        wx = min(x + rect.x, x + rect2.width - rect3.width)
        wy = y + rect.y #+ rect.height

        return (wx, wy)

    def __draw_window_border(self, widget):
        """ toggle windows have no decoration, we draw the border ourselvtoggleWindowClose(es """
        window = widget.bin_window
        g = window.get_geometry()
        width = g[2]
        height = g[3]
        gc = window.new_gc()
        brown = widget.get_colormap().alloc_color('#AAAAA3')
        gc.set_foreground(brown)
        window.draw_rectangle(gc, False, 0, 0, width - 1, height - 1)

    def __toggle_window_close(self, restoreLabel=True):
        """ Close toggle window """
        if self.__toggle_window_close_recursive: return
        if self.__toggled_triple:
            if restoreLabel: self.__toggled_triple[0].set_label(self.__toggled_button_label)
            self.__toggled_triple[1].hide()
            # this will invoke on_togglebutton_clicked and then this method recursive again!
            self.__toggle_window_close_recursive = True
            self.__toggled_triple[0].set_active(False)
            self.__toggle_window_close_recursive = False
            self.__toggled_triple = None

    def __refresh_globals(self):
        """ Sets the global groove and global tempo labels """
        if self.__gui.get_current_bar_number() == 0:
            groove = self.__song.get_data().get_bar_info(0).get_groove()
            self.__eventGroove.set_label_from_event(self.__togglebutton1, groove)
            tempo = self.__song.get_data().get_bar_info(0).get_tempo()
            self.__eventTempo.set_label_from_event(self.__togglebutton2, tempo)
