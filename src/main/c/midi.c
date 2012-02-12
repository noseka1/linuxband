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
#include <stdio.h>
#include <stdlib.h>
#include <sys/types.h>
#include <sys/time.h>
#include <unistd.h>
#include <assert.h>
#include <string.h>
#include <sysexits.h>
#include <errno.h>
#include <signal.h>
#include <jack/jack.h>
#include <jack/midiport.h>
#include <glib.h>
#include "config.h"
#include "smf.h"
#include "midi.h"

int
strcmp_min(char *s1, char *s2) {
	int len = strlen(s1) < strlen(s2) ? strlen(s1) : strlen(s2);
	return strncmp(s1, s2, len);
}

char * skip_marker_tag(char *event) {
	if (strcmp_min(event, MARKER_TAG) == 0)
		return event + strlen(MARKER_TAG);
	else
		return NULL;
}

char *
decode_barnum(char *event) {
	char *s = event;
	if ((s = skip_marker_tag(s)) != NULL) {
		if (strcmp_min(s, BAR_TAG) == 0) {
			return s + strlen(BAR_TAG);
		}
	}
	return NULL;
}

char *
decode_linenum(char *event) {
	char *s = event;
	if ((s = skip_marker_tag(s)) != NULL) {
		if (isdigit(*s)) {
			return s;
		}
	}
	return NULL;
}

char *
decode_end(char *event) {
	char *s = event;
	if ((s = skip_marker_tag(s)) != NULL) {
		if (strcmp_min(s, END_TAG) == 0) {
			return s;
		}
	}
	return NULL;
}

void
show_track(smf_track_t *track) {
	g_debug("TRACK %i\n", track->track_number);
	int i = 1;
	smf_event_t *event;
	while ((event = smf_track_get_event_by_number(track, i)) != NULL) {
		g_debug("%6i %s\n", event->time_pulses, smf_event_decode(event));
		i++;
	}
}

void
show_smf(smf_t *smf) {
	g_debug("%s\n", smf_decode(smf));
	int i = 1;
	smf_track_t *track;
	while ((track = smf_get_track_by_number(smf, i)) != NULL) {
		show_track(track);
		i++;
	}
}

smf_event_t *
find_song_end(smf_t *smf) {
	smf_event_t *event = NULL, *end = NULL;
	while ((event = smf_get_next_event(smf)) != NULL) {
		if (smf_event_is_metadata(event)) {
			char *decoded = smf_event_decode(event);
			if (decode_end(decoded) != NULL) {
				end = event;
			}
			free(decoded);
		}
		if (end != NULL) break;
	}
	assert(end);
	return(end);
}

smf_event_t *
find_bar_end(smf_t *smf) {
	smf_event_t *event = NULL, *end = NULL;
	while ((event = smf_get_next_event(smf)) != NULL) {
		if (smf_event_is_metadata(event)) {
			char *decoded = smf_event_decode(event);
			if ((decode_barnum(decoded)) != NULL || (decode_end(decoded)) != NULL) {
				end = event;
			}
			free(decoded);
		}
		if (end != NULL) break;
	}
	assert(end);
	return(end);
}

smf_event_t *
find_bar_num(smf_t *smf, int barnum) {
	smf_event_t *event = NULL, *start = NULL;
	while ((event = smf_get_next_event(smf)) != NULL) {
		if (smf_event_is_metadata(event)) {
			char *decoded = smf_event_decode(event);
			char *s;
			if ((s = decode_barnum(decoded)) != NULL) {
				if (atoi(s) == barnum){
					start = event;
				}
			}
			free(decoded);
		}
		if (start != NULL) break;
	}
	assert(start);
	return(start);
}

double
find_bar_num_seconds(smf_t *smf, int barnum) {
	smf_rewind(smf);
	smf_event_t *event = find_bar_num(smf, barnum);
	return event->time_seconds;
}

void
get_bar_offsets(smf_t *smf, int barnum, int result[2]) {
	smf_rewind(smf);
	smf_event_t *start = find_bar_num(smf, barnum);
	smf_event_t *end = find_bar_end(smf);
	result[0] = start->time_pulses;
	result[1] = end->time_pulses;
}

smf_event_t *
copy_event(smf_event_t *event) {
	char *buff = event->midi_buffer;
	int len = event->midi_buffer_length;
	return smf_event_new_from_pointer(buff, len);
}

void
copy_events(smf_t *smf, smf_t *smf2, int start, int end, int start2) {
	int ret = smf_seek_to_pulses(smf, start);
	assert(ret == 0);
	smf_event_t *event;
	while ((event = smf_get_next_event(smf)) != NULL && event->time_pulses < end) {
		int time = event->time_pulses;
		int track_num = event->track_number;
		smf_track_t *track = smf_get_track_by_number(smf2, track_num);
		smf_track_add_event_pulses(track, copy_event(event), start2 + time - start);
	}
}

smf_event_t *
create_marker(char *text) {
	char meta_type = 0xFF;
	char marker_type = 0x06;
	int text_len = strlen(text);
	smf_event_t *event = smf_event_new();
	event->midi_buffer_length = 3 + text_len;
	event->midi_buffer = malloc(event->midi_buffer_length);
	event->midi_buffer[0] = meta_type;
	event->midi_buffer[1] = marker_type;
	event->midi_buffer[2] = text_len;
	memcpy(event->midi_buffer + 3, text, text_len);
	return event;
}

smf_t *
create_empty_smf(smf_t *smf) {
	smf_t *smf2 = smf_new();
	int ret = smf_set_ppqn(smf2, smf->ppqn);
	assert(ret == 0);
	ret = smf_set_format(smf2, smf->format);
	assert(ret == 0);

	// create tracks
	int i;
	for (i = 0; i < smf->number_of_tracks; i++) {
		smf_track_t *track = smf_track_new();
		smf_add_track(smf2, track);
	}
	return smf2;
}

smf_t *
copy_smf(smf_t *smf) {
	smf_t *smf2 = create_empty_smf(smf);
	copy_events(smf, smf2, 0, INT_MAX, 0);
	return smf2;
}

smf_t *
copy_smf_bars(smf_t *smf, int bar_start, int bar_end) {

	smf_t *smf2 = create_empty_smf(smf);

	// copy time 0 meta events
	smf_rewind(smf);
	smf_track_t *meta_track = smf_get_track_by_number(smf, 1);
	smf_track_t *meta_track2 = smf_get_track_by_number(smf2, 1);
	assert(meta_track);
	assert(meta_track2);
	smf_event_t * event;
	while ((event = smf_track_get_next_event(meta_track)) != NULL && event->time_pulses == 0) {
			if (decode_barnum(smf_event_decode(event)) == NULL) {
				smf_event_t * new_event = copy_event(event);
				smf_track_add_event_pulses(meta_track2, new_event, 0);
			}
	}

	// copy bars
	int i;
	int start2 = 0;
	for (i = bar_start; i <= bar_end; i++) {
		int offsets[2];
		get_bar_offsets(smf, i, offsets);
		int start = offsets[0], end = offsets[1];
		copy_events(smf, smf2, start, end, start2);
		start2 += end - start;
	}

	// end of the song event
	smf_event_t *end = create_marker(END_TAG);
	smf_track_add_event_pulses(meta_track2, end, start2);
	return smf2;
}


void
loop_smf(smf_t *smf, int intro_length, int tags[], double tags_secs[]) {
	smf_rewind(smf);
	int i;
	// find end of introduction
	for (i = 0; i <= intro_length; i++) {
		smf_event_t *intro_end = find_bar_end(smf);
		tags[0] = intro_end->time_pulses;
		tags_secs[0] = intro_end->time_seconds;
	}
	// find end of song
	smf_rewind(smf);
	smf_event_t *song_end = find_song_end(smf);
	tags[1] = song_end->time_pulses;
	tags_secs[1] = song_end->time_seconds;
	// compute song length
	tags[2] = tags[1] - tags[0];
	tags_secs[2] = tags_secs[1] - tags_secs[0];
	// copy it after the end of song
	copy_events(smf, smf, tags[0], tags[1], tags[1]);
	// end of the song event
	smf_event_t *end_event = create_marker(END_TAG);
	smf_track_t *meta_track = smf_get_track_by_number(smf, 1);
	assert(meta_track);
	smf_track_add_event_pulses(meta_track, end_event, tags[1] + tags[2]);
}

smf_t *
load_smf_data(char *buffer, int length) {
	smf_t *smf = smf_load_from_memory(buffer, length);
	if (smf == NULL) {
		g_error("Loading of SMF file failed.");
	}
	g_debug("%s.", smf_decode(smf));
	return smf;
}
