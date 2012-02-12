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

import threading
import os
import fcntl
import select
import subprocess
import gobject
import logging
from linuxband.glob import Glob

class MidiPlayer:

    __COMM_LOAD = "LOAD"
    __COMM_PLAY = "PLAY"
    __COMM_PLAY_BAR = "PLAY_BAR"
    __COMM_PLAY_BARS = "PLAY_BARS"
    __COMM_STOP = "STOP"
    __COMM_PAUSE_ON = "PAUSE_ON"
    __COMM_PAUSE_OFF = "PAUSE_OFF"
    __COMM_LOOP_ON = "LOOP_ON"
    __COMM_LOOP_OFF = "LOOP_OFF"
    __COMM_JACK_TRANSPORT_ON = "TRANSPORT_ON"
    __COMM_JACK_TRANSPORT_OFF = "TRANSPORT_OFF"
    __COMM_INTRO_LENGTH = "INTRO_LENGTH"
    __COMM_FINISH = "FINISH"

    __EVENT_BAR_NUM = "BAR_NUMBER"
    __EVENT_LINE_NUM = "LINE_NUMBER"
    __EVENT_SONG_END = "SONG_END"

    __SEPARATOR = ' '

    def __init__(self, gui):
        self.__gui = gui
        self.__mma_line_offset = 0
        self.__player = None
        self.__receive_thread = None
        self.__piper = None
        self.__pipew = None
        self.__pout = None

        self.__saved_intro_length = 2
        self.__saved_pause = False
        self.__saved_loop = True
        self.__saved_transport = True
        self.__saved_midi_data = None
        self.__saved_offset = None

        self.__playing = False
        self.__connected = False

    def startup(self):
        piper, pipew = os.pipe()
        self.__piper = piper
        self.__pipew = pipew

        pipeName = '/proc/' + str(Glob.PID) + '/fd/' + str(pipew)
        command = [ Glob.PLAYER_PROGRAM, '-s', '-n', '-x', pipeName ]
        if Glob.CONSOLE_LOG_LEVEL == logging.DEBUG:
            command.insert(1, '-d')
        try:
            self.__player = subprocess.Popen(command, stdin=subprocess.PIPE)
        except:
            logging.exception("Failed to run command '%s'", ' '.join(command))
            os.close(piper)
            os.close(pipew)
            return
        # sending data to midi player should not block    
        out = self.__player.stdin.fileno()
        flags = fcntl.fcntl(out, fcntl.F_GETFL)
        fcntl.fcntl(out, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        self.__pout = out
        # start receive thread listening for incoming events
        self.__receive_thread = threading.Thread(target=self.__receive_data)
        self.__receive_thread.start()
        self.__connected = True
        self.__resend_data()

    def shutdown(self):
        if self.__receive_thread:
            os.write(self.__pipew, MidiPlayer.__COMM_FINISH + MidiPlayer.__SEPARATOR)
            self.__receive_thread.join()
            self.__receive_thread = None
        if self.__player:
            self.playback_stop()
            self.__send_token(MidiPlayer.__COMM_FINISH)
            self.__player.wait()
            self.__player = None
        # descriptors could have been already closed
        try:
            os.close(self.__piper)
        except:
            pass
        try:
            os.close(self.__pipew)
        except:
            pass
        try:
            os.close(self.__pout)
        except:
            pass

    def load_smf_data(self, midi_data, offset):
        self.__mma_line_offset = offset
        self.__send_token(MidiPlayer.__COMM_LOAD)
        self.__send_token(str(len(midi_data)))
        self.__send_data(midi_data)
        self.__saved_midi_data = midi_data
        self.__saved_offset = offset

    def playback_start(self):
        self.__send_token(MidiPlayer.__COMM_PLAY)
        self.__saved_pause = False

    def playback_start_bar(self, bar):
        self.__send_token(MidiPlayer.__COMM_PLAY_BAR)
        self.__send_token(str(bar))
        self.__saved_pause = False

    def playback_start_bars(self, bars):
        self.__send_token(MidiPlayer.__COMM_PLAY_BARS)
        self.__send_token(str(bars[0]))
        self.__send_token(str(bars[1]))
        self.__saved_pause = False

    def playback_stop(self):
        self.__send_token(MidiPlayer.__COMM_STOP)
        self.__saved_pause = False

    def set_pause(self, pause):
        comm = MidiPlayer.__COMM_PAUSE_ON if pause else MidiPlayer.__COMM_PAUSE_OFF
        self.__send_token(comm)
        self.__saved_pause = pause

    def set_loop(self, loop):
        comm = MidiPlayer.__COMM_LOOP_ON if loop else MidiPlayer.__COMM_LOOP_OFF
        self.__send_token(comm)
        self.__saved_loop = loop

    def use_jack_transport(self, transport):
        comm = MidiPlayer.__COMM_JACK_TRANSPORT_ON if transport else MidiPlayer.__COMM_JACK_TRANSPORT_OFF
        self.__send_token(comm)
        self.__saved_transport = transport

    def set_intro_length(self, length):
        self.__send_token(MidiPlayer.__COMM_INTRO_LENGTH)
        self.__send_token(str(length))
        self.__saved_intro_length = length

    def is_playing(self):
        return self.__playing

    def __resend_data(self):
        if self.__saved_midi_data != None:
            self.load_smf_data(self.__saved_midi_data, self.__saved_offset)
        self.set_intro_length(self.__saved_intro_length)
        self.set_pause(self.__saved_pause)
        self.set_loop(self.__saved_loop)
        self.use_jack_transport(self.__saved_transport)

    def __read_token(self, pipe):
        token = []
        ch = os.read(pipe, 1)
        while ch != MidiPlayer.__SEPARATOR:
            token.append(ch)
            ch = os.read(pipe, 1)
        token = ''.join(token)
        logging.debug(token)
        return ''.join(token)

    def __receive_data(self):
        while True:
            logging.debug("Waiting for events")
            token = self.__read_token(self.__piper)
            if token == MidiPlayer.__EVENT_BAR_NUM:
                # move the playhead to the new position
                bar_num = int(self.__read_token(self.__piper))
                gobject.idle_add(self.__gui.move_playhead_to_bar, bar_num)
                self.__playing = True
            elif token == MidiPlayer.__EVENT_LINE_NUM:
                # move the playhead2 to the new position 
                lineNum = int(self.__read_token(self.__piper))
                gobject.idle_add(self.__gui.move_playhead_to_line, lineNum - self.__mma_line_offset - 1)
                self.__playing = True
            elif token == MidiPlayer.__EVENT_SONG_END:
                # playback has finished
                gobject.idle_add(self.__gui.hide_playhead)
                self.__playing = False
            elif token == MidiPlayer.__COMM_FINISH:
                logging.debug("Thread finishing")
                return
            else:
                logging.debug("Unrecognized data '%s'", token)

    def __send_token(self, comm):
        logging.debug(comm)
        self.__send_data(comm)
        self.__send_data(MidiPlayer.__SEPARATOR)

    def __send_data(self, data):
        if self.__connected:
            logging.debug("Sending %i bytes", len(data))
            try:
                timeout = 2
                if not select.select([], [self.__pout], [], timeout)[1]:
                    logging.error("Cannot send data to midi player. Timeout after " \
                              + str(timeout) + " seconds.")
                else:
                    os.write(self.__pout, data)
            except:
                logging.error("Failed to send data to midi player. Ensure the JACK server is running and hit the JACK reconnect button.")
        else:
            logging.debug("Not yet connected.")
