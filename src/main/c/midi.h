/*
 * Copyright (c) 2012 Ales Nosek <ales.nosek@gmail.com>
 *
 * This file is part of LinuxBand.
 *
 * LinuxBand is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <http://www.gnu.org/licenses/>.
 */
#ifndef JACKSMFPLAYERMIDI_H_
#define JACKSMFPLAYERMIDI_H_

#define MARKER_TAG	"Marker: "
#define BAR_TAG	"BAR"
#define END_TAG	"END"

char *
decode_barnum(char *event);

char *
decode_linenum(char *event);

void
show_smf(smf_t *smf);

double
find_bar_num_seconds(smf_t *smf, int barnum);

void
get_bar_offsets(smf_t *smf, int barnum, int result[2]);

smf_t *
copy_smf(smf_t *smf);

smf_t *
copy_smf_bars(smf_t *smf, int bar_start, int bar_end);

void
loop_smf(smf_t *smf, int intro_length, int tags[], double tags_secs[]);

smf_t *
load_smf_data(char *buffer, int length);

char *
decode_end(char *event);


#endif /* JACKSMFPLAYERMIDI_H_ */
