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
import pickle
import logging
import fnmatch
import os
from linuxband.glob import Glob
from linuxband.mma.parse import parse
from linuxband.mma.bar_info import BarInfo


class Grooves(object):

    __grooves_cache_file = Glob.CONFIG_DIR + '/grooves.cache'

    def __init__(self, config):
        self.__config = config
        self.__grooves_model = None

    def load_grooves(self, use_cache):
        self.__grooves_model = None
        if use_cache:
            self.__grooves_model = self.__load_grooves_from_cache()
        if not self.__grooves_model:
            self.__grooves_model, grooves_list = self.__load_grooves()
            self.__cache_grooves(grooves_list)

    def get_grooves_model(self):
        return self.__grooves_model

    def __groove_compare(self, x, y):
        a = x[0].upper()
        b = y[0].upper()
        if a > b:
            return 1
        elif a == b:
            return 0
        else: # x<y
            return -1

    def __create_grooves_model(self, grooves_list):
        """
        The model is used for Groove selection dialog.
        """
        grooves_model = gtk.ListStore(str, str, str, str, str, str, gtk.ListStore)
        sub_liststore = None
        pgroove = None
        march_sub_liststore = None
        for index, groove in enumerate(grooves_list):
            if groove[0].startswith('MilIntro'):
                # hack for MilIntro2, MilIntro4 to put them under March
                march_sub_liststore.append(groove)
            elif index == 0 \
                    or not groove[0].upper().startswith(pgroove) \
                    or groove[0].startswith('Metronome'):   # metronome hack    
                sub_liststore = gtk.ListStore(str, str, str, str, str, str)
                grooves_model.append(groove + [ sub_liststore ])
                pgroove = groove[0].upper()
                # March hack
                if groove[0] == 'March':
                    march_sub_liststore = sub_liststore
            else:
                sub_liststore.append(groove)
        return grooves_model

    def __load_grooves(self):
        """ 
        Load grooves from /usr/share/mma/lib/stdlib (configurable).
        
        Sort grooves and store them in grooves_list
        Call __create_grooves_model()
        """
        grooves_list = []
        self.__do_load_grooves(grooves_list, self.__config.get_mma_grooves_path())
        grooves_list.sort(self.__groove_compare)
        return self.__create_grooves_model(grooves_list), grooves_list

    def __do_load_grooves(self, grooves_list, path):
        """
        Load grooves and recurse into subdirectories.
        """
        for dirname, dirnames, filenames in os.walk(path): #@UnusedVariable            
            for name in filenames:
                if fnmatch.fnmatch(name, '*.mma'):
                    full_name = os.path.join(dirname, name)
                    song_data = self.__parseGrooves(full_name)
                    if not song_data: continue
                    song_bar_info = song_data.get_bar_info_all()
                    for line in song_bar_info[0].get_lines():
                        action = line[0]
                        if action == Glob.A_BEGIN_BLOCK and line[1] == Glob.A_DOC:
                            doc = BarInfo.get_doc_value(line)
                        elif action == Glob.A_AUTHOR:
                            author = BarInfo.get_author_value(line)
                        elif action == Glob.A_TIME:
                            time = BarInfo.get_time_value(line)
                        elif action == Glob.A_DEF_GROOVE:
                            gname, gdesc = BarInfo.get_defgroove_value(line)
                            grooves_list.append([gname, doc, gdesc, author, time, full_name])
            for name in dirnames:
                path = os.path.join(dirname, name)
                self.__do_load_grooves(grooves_list, path)

    def __parseGrooves(self, file_name):
        song_data = None
        logging.debug("Opening groove file '%s'" % file_name)
        try:
            mma_file = file(file_name, 'r')
            try:
                song_data = parse(mma_file)
            except ValueError:
                logging.exception("Failed to parse the file.")
            mma_file.close()
        except:
            logging.exception("Failed to load grooves from file '" + file_name + "'")
        return song_data

    def __load_grooves_from_cache(self):
        """
        Load grooves from file or cache.
        
        Call createGroovesModel()
        """
        fname = Grooves.__grooves_cache_file
        try:
            infile = file(fname, 'r')
            try:
                grooves_list = pickle.load(infile)
            finally:
                infile.close()
        except:
            logging.exception("Unable to load grooves from cache '" + fname + "'")
            return
        logging.info("Loaded %d groove patterns from cache '%s'" % (len(grooves_list), fname))
        return self.__create_grooves_model(grooves_list)

    def __cache_grooves(self, grooves_list):
        """
        Store the grooves_list into cache file.
        """
        fname = Grooves.__grooves_cache_file
        logging.info("Stored %d groove patterns in cache '%s'" % (len(grooves_list), fname))
        try:
            outfile = file(fname, 'w')
            try:
                pickle.dump(grooves_list, outfile, True)
            finally:
                outfile.close()
        except:
            logging.exception("Unable to store grooves into cache '" + fname + "'")
