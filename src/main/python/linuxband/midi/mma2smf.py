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
import select
import subprocess
import string
from linuxband.glob import Glob
import logging


class MidiGenerator(object):

    def __init__(self, config):
        self.__config = config

    def check_mma_syntax(self, mma_data):
        """
        < -1 other error, = -1 MMA error unknown line, 0 is OK, > 0 MMA error line
        """
        mmainput = '/proc/self/fd/0'
        command = [ self.__config.get_mma_path(), mmainput, '-n' ] # -n No generation of midi output
        try:
            mma = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        except:
            logging.exception("Failed to run command '" + ' '.join(command) + "'")
            return -2
        try:
            fout = mma.stdin
            fout.write(mma_data)
            fout.close()
        except:
            logging.exception("Failed to send data to MMA")
            return -2
        exit_status = mma.wait()
        if (exit_status != 0):
            logging.error("Failed generating midi data. MMA returned status code " + str(exit_status))
            outstr = mma.stdout.readlines()
            num = self.__parse_error_line_number(outstr)
            logging.error(''.join(outstr))
            return num
        return 0

    def generate_smf(self, mma_data):
        """
        Convert mma_data string into midi_data string using MMA program.
        """
        piper, pipew = os.pipe()
        try:
            res_and_midi = self.__do_generate_smf(piper, pipew, mma_data)
        finally:
            try:
                os.close(piper)
            except:
                pass
            try:
                os.close(pipew)
            except:
                pass
        return res_and_midi

    def __do_generate_smf(self, piper, pipew, mma_data):
        """
        < -1 other error, = -1 MMA error unknown line, 0 is OK, > 0 MMA error line
        """
        mmainput = '/proc/self/fd/0'
        mmaoutput = '/proc/' + str(Glob.PID) + '/fd/' + str(pipew)
        command = [ self.__config.get_mma_path(), mmainput, '-f' , mmaoutput ]
        try:
            mma = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        except:
            logging.exception("Failed to run command '" + ' '.join(command) + "'")
            return (-2, '')
        try:
            fout = mma.stdin
            fout.write(mma_data)
            fout.close()
        except:
            logging.exception("Failed to send data to MMA")
            return (-2, '')
        try:
            fin = os.fdopen(piper, 'r')
            timeout = 2
            if not select.select([fin], [], [], timeout)[0]:
                logging.error("MMA generated no output. Timeout after " + str(timeout) + " seconds.")
                outstr = mma.stdout.readlines()
                logging.error(' '.join(outstr))
                return (-1, '')
            os.close(pipew) # close our write pipe end, now only MMA has it opened
            midi_data = fin.read()
        except:
            logging.exception("Failed to read midi data from MMA")
        exit_status = mma.wait()
        if (exit_status != 0):
            logging.error("Failed generating midi data. MMA returned status code " + str(exit_status))
            return (-2, '')
        return (0, midi_data)

    def __parse_error_line_number(self, lines):
        """ 
        Parse out the error line number. Error line example: ERROR:<Line 23><File:/proc/self/fd/0>
        """
        for i, line in enumerate(lines): #@UnusedVariable
            res = string.find(line, "ERROR")
            if res != -1: break
        if res == -1: return -1
        start = string.find(line, "<")
        end = string.find(line, ">")
        if start == -1 or end == -1: return -1
        lmidd = line[start + 1: end]
        midds = lmidd.split()
        if len(midds) != 2: return -1
        try:
            return int(midds[1])
        except TypeError:
            return -1
