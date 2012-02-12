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
#include <fcntl.h>
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
#include <pthread.h>
#include "smf.h"
#include "remote_control.h"
#include "midi.h"

FILE *input_pipe = NULL;
FILE *output_pipe = NULL;

#define MAX_TOKEN_LENGTH 	30
#define TOKEN_SEPARATOR	' '

typedef enum {
	LOAD,
	PLAY,
	PLAY_BAR,
	PLAY_BARS,
	STOP,
	PAUSE_ON,
	PAUSE_OFF,
	LOOP_ON,
	LOOP_OFF,
	TRANSPORT_ON,
	TRANSPORT_OFF,
	INTRO_LENGTH,
	FINISH,
	UNKNOWN
} COMMAND;

#define COMMAND_MAP_SIZE	UNKNOWN
char *command_map[COMMAND_MAP_SIZE];

void init_command_map() {
	command_map[LOAD] = "LOAD";
	command_map[PLAY] = "PLAY";
	command_map[PLAY_BAR] = "PLAY_BAR";
	command_map[PLAY_BARS] = "PLAY_BARS";
	command_map[STOP] = "STOP";
	command_map[PAUSE_ON] = "PAUSE_ON";
	command_map[PAUSE_OFF] = "PAUSE_OFF";
	command_map[LOOP_ON] = "LOOP_ON";
	command_map[LOOP_OFF] = "LOOP_OFF";
	command_map[TRANSPORT_ON] = "TRANSPORT_ON";
	command_map[TRANSPORT_OFF] = "TRANSPORT_OFF";
	command_map[INTRO_LENGTH] = "INTRO_LENGTH";
	command_map[FINISH] = "FINISH";
}

#define FEEDBACK_BARNUM	"BAR_NUMBER"
#define FEEDBACK_LINENUM	"LINE_NUMBER"
#define FEEDBACK_SONGEND	"SONG_END"

#define PARTIAL_SEEK_LENGTH	10

extern smf_t * volatile smf_vol;
extern jack_client_t *jack_client;
extern volatile int use_transport;
extern volatile int playback_started;
extern volatile int song_position;
extern volatile int playback_paused;

static smf_t *orig_smf = NULL; // smf data as received from client
static volatile int loop = 1; // should loop?
static int intro_bar_length = 2; // intro bars count
static int tags[3]; // end of intro, end of the song, length of song (all in pulses)
static double tags_secs[3]; // the same in seconds
static int loop_count = 0;
static double loop_offset = 0;

extern jack_nframes_t
seconds_to_nframes(double seconds);

pthread_mutex_t mutex;

void
open_pipes(char *output_pipe_name) {
    input_pipe = fdopen(0, "r");
    if (!input_pipe) {
    	g_error("Cannot open stdin for reading. %s", strerror(errno));
    }
    g_debug("Input pipe: stdin");
    int output_pipe_fd = open(output_pipe_name, O_WRONLY | O_NONBLOCK);
    if (output_pipe_fd == -1) {
            g_error("Failed to open output pipe '%s'. %s", output_pipe_name, strerror(errno));
    }
    else {
    	output_pipe = fdopen(output_pipe_fd, "w");
    	if (!output_pipe){
          g_error("%s", strerror(errno));
    	}
    }
    g_debug("Output pipe: '%s'", output_pipe_name);
}

void
next_token(FILE *pipe, char* buffer) {
	memset(buffer, 0, MAX_TOKEN_LENGTH);
	int i = 0;
	char c = -1;
	while (c != TOKEN_SEPARATOR && i < MAX_TOKEN_LENGTH - 1) {
		if (fread(&c, sizeof(c), 1, pipe) != 1) break;
		buffer[i] = c;
		i++;
	}
	buffer[--i] = 0;
}

COMMAND
next_command(FILE *pipe) {
	char token[MAX_TOKEN_LENGTH];
	next_token(pipe, token);
	int i;
	for (i = 0; i < COMMAND_MAP_SIZE; i++) {
		if (strcmp(token, command_map[i]) == 0) return i;
	}
	return UNKNOWN;
}

double
loop_song(smf_t *smf) {
	int intro_end = tags[0];
	int song_end = tags[1];
	int song_length = tags[2];
	smf_event_t *event = smf_peek_next_event(smf);
	int next = event->time_pulses;
	if (loop) {
		if (next > song_end) {
			// g_debug("SONG_LENGTH %i", song_length);
			// g_debug("NEXT %i", next);
			g_debug("LOOP. Seeking to %d pulses.", next - song_length);
			int ret = smf_seek_to_pulses(smf, next - song_length);
			assert(ret == 0);
			smf_event_t *event2 = smf_peek_next_event(smf);
			loop_offset = (event->time_seconds - event2->time_seconds) * ++loop_count;
			// g_debug("Event1 = %lf, event2 = %lf", event->time_seconds, event2->time_seconds);
		}
	}
	// g_debug("OFFSET %f", loop_offset);
	return loop_offset;
}

int
check_event(smf_event_t *event, double seconds) {
	if (event == NULL) {
		g_critical("Trying to seek past the end of song.");
		return TRUE;
	}
	else {
		return event->time_seconds >= seconds;
	}
}

int
partial_seek(smf_t *smf, double seconds) {
	smf_event_t* event = smf_peek_next_event(smf);
	// g_debug("Partial seek enter: TARGET %f, CURRENT %f", seconds, event->time_seconds);
	if (event == NULL || event->time_seconds >= seconds) {
		smf_rewind(smf);
	}

	// check first event
	event = smf_peek_next_event(smf);
	if (check_event(event, seconds)) {
		g_debug("TARGET %f, CURRENT %f", seconds, event->time_seconds);
		return TRUE;
	}

	int i = 0;
	while (i < PARTIAL_SEEK_LENGTH) {
		smf_event_t *ret = smf_get_next_event(smf);
		assert(ret != 0);
		event = smf_peek_next_event(smf);
		if (check_event(event, seconds)) {
			g_debug("TARGET %f, CURRENT %f", seconds, event->time_seconds);
			return TRUE;
		}
		i++;
	}
	g_debug("TARGET %f, CURRENT %f", seconds, event->time_seconds);
	return FALSE;
}

int
loop_seek(smf_t *smf, double seconds) {
	double intro_end = tags_secs[0];
	double song_end = tags_secs[1];
	double song_length = tags_secs[2];
	// g_debug("LOOP_SEEK CALLED");
	// g_debug("INTRO_END=%f, SONG_END=%f, SONG_LENGTH=%f", intro_end, song_end, song_length);
	g_debug("SECONDS = %f", seconds);
	loop_count = 0;
	loop_offset = 0;
	if (seconds > song_end) {
		while (seconds > intro_end + (loop_count + 1) * song_length) {
			loop_count++;
			// g_debug("LOOP_COUNT++");
		}
		loop_offset = loop_count * song_length;
		seconds = seconds - loop_offset;
		// g_debug("LOOP_OFFSET %f", loop_offset);
	}
	// g_debug("LOOP_COUNT %i, LOOP_OFFSET %f", loop_count, loop_offset);
	return partial_seek(smf, seconds);
}

void
free_smf() {
	if (smf_vol != NULL && smf_vol != orig_smf) smf_delete(smf_vol);
}

void
start_playback() {
	loop_count = 0;
	loop_offset = 0;
	g_debug("Use transport %i", use_transport);
	if (use_transport) {
		jack_transport_start(jack_client);
	}
	else {
		playback_started = jack_frame_time(jack_client);
	}
	playback_paused = 0;
}

void
command_load(FILE *pipe) {
	char token[MAX_TOKEN_LENGTH];
	next_token(pipe, token);
	int count = atoi(token);
	g_debug("MIDI data length = %i", count);
	char *buff = (char *) malloc(count);
	int read = fread(buff, sizeof(char), count, pipe);
	if (read < count) {
		g_error("Error while reading MIDI data. Marker: Expected %i bytes, read %i.", count, read);
	}
	g_debug("MIDI data %i bytes read", count);
	if (orig_smf != NULL) smf_delete(orig_smf);
	orig_smf = load_smf_data(buff, count);
	free(buff);
}

void
command_stop() {
	if (use_transport) {
		jack_transport_stop(jack_client);
		send_sond_end();
	}
	else {
		playback_started = -1;
	}
	playback_paused = 0;
}

void
command_play() {
	command_stop();
	pthread_mutex_lock(&mutex);
	smf_t *smf = copy_smf(orig_smf);
	pthread_mutex_unlock(&mutex);
	loop_smf(smf, intro_bar_length, tags, tags_secs);
	smf_rewind(smf);
	pthread_mutex_lock(&mutex);
	free_smf();
	smf_vol = smf;
	pthread_mutex_unlock(&mutex);
	if (use_transport) {
		jack_transport_locate(jack_client, 0);
	}
	else {
		song_position = 0;
	}
	start_playback();
}

void
command_play_from_bar(FILE *pipe) {
	char token[MAX_TOKEN_LENGTH];
	next_token(pipe, token);
	int start = atoi(token);
	g_debug("PLAYING FROM BAR %i", start);
	command_stop();
	pthread_mutex_lock(&mutex);
	smf_t *smf = copy_smf(orig_smf);
	pthread_mutex_unlock(&mutex);
	loop_smf(smf, intro_bar_length, tags, tags_secs);
	smf_rewind(smf);
	double start_time = find_bar_num_seconds(smf, start);
	g_debug("START_TIME = %f", start_time);
	pthread_mutex_lock(&mutex);
	free_smf();
	smf_vol = smf;
	if (use_transport) {
		jack_transport_locate(jack_client, seconds_to_nframes(start_time));
	}
	else {
		int ret = smf_seek_to_seconds(smf, start_time);
		assert(ret == 0);
		song_position = seconds_to_nframes(start_time);
	}
	pthread_mutex_unlock(&mutex);
	start_playback();
}

void
command_play_bars(FILE *pipe) {
	char token[MAX_TOKEN_LENGTH];
	next_token(pipe, token);
	int start = atoi(token);
	next_token(pipe, token);
	int end = atoi(token);
	command_stop();
	pthread_mutex_lock(&mutex);
	smf_t *smf = copy_smf_bars(orig_smf, start, end);
	pthread_mutex_unlock(&mutex);
	loop_smf(smf, 0, tags, tags_secs);
	smf_rewind(smf);
	pthread_mutex_lock(&mutex);
	free_smf();
	smf_vol = smf;
	pthread_mutex_unlock(&mutex);
	if (use_transport) {
		jack_transport_locate(jack_client, 0);
	}
	else {
		song_position = 0;
	}
	start_playback();
}

void
command_pause(int on) {
	if (on) {
		if (use_transport && !playback_paused) {
			jack_transport_stop(jack_client);
		}
		playback_paused = 1;
	}
	else {
		if (use_transport && playback_paused) {
			jack_transport_start(jack_client);
		}
		playback_paused = 0;
	}
}

void
command_loop(int on) {
	loop = on;
}

void
command_transport(int on) {
	use_transport = on;
}

void
command_intro_length(FILE *pipe) {
	char token[MAX_TOKEN_LENGTH];
	next_token(pipe, token);
	intro_bar_length = atoi(token);
	g_debug("Intro length = %i", intro_bar_length);
}

void
command_finish() {
	jack_client_close(jack_client);
	exit(0);
}

/**
 * This is the shutdown callback for this JACK application.
 * It is called by JACK if the server ever shuts down or
 * decides to disconnect the client.
 */
 void
 jack_shutdown(void *arg)
 {
	 g_debug("Jack shutdown.");
	 exit(EX_UNAVAILABLE);
 }

void
remote_control_loop(FILE *input_pipe, FILE *output_pipe) {
	int loop = 1;
	while (loop) {
		COMMAND command = next_command(input_pipe);
		switch(command) {
		case LOAD:
			g_debug("Load");
			command_load(input_pipe);
			break;
		case PLAY:
			g_debug("Play");
			command_play();
			break;
		case PLAY_BAR:
			g_debug("Play from bar");
			command_play_from_bar(input_pipe);
			break;
		case PLAY_BARS:
			g_debug("Play bars");
			command_play_bars(input_pipe);
			break;
		case STOP:
			g_debug("Stop");
			command_stop();
			break;
		case PAUSE_ON:
			g_debug("Pause On");
			command_pause(1);
			break;
		case PAUSE_OFF:
			g_debug("Pause Off");
			command_pause(0);
			break;
		case LOOP_ON:
			g_debug("Loop On");
			command_loop(1);
			break;
		case LOOP_OFF:
			g_debug("Loop Off");
			command_loop(0);
			break;
		case TRANSPORT_ON:
			g_debug("Transport On");
			command_transport(1);
			break;
		case TRANSPORT_OFF:
			g_debug("Transport Off");
			command_transport(0);
			break;
		case INTRO_LENGTH:
			g_debug("Intro Length");
			command_intro_length(input_pipe);
			break;
		case FINISH:
			g_debug("Finish");
			command_finish();
			break;
		case UNKNOWN:
			g_error("Received unknown command. Exiting ...");
			break;
		}
	}
}

void
remote_control_start(char *output_pipe_name) {
	open_pipes(output_pipe_name);
	init_command_map();
	remote_control_loop(input_pipe, output_pipe);
}

void
send_token(char *token) {
	int res = fprintf(output_pipe, "%s ", token);
	if (res == -1)
		g_error("Failed to send token %s. %s", token, strerror(errno));
	fflush(output_pipe);
}

int
process_meta_event(char *event) {
	// tell the controller to move its play head
	char *s;
	if ((s = decode_barnum(event)) != NULL) {
		send_token(FEEDBACK_BARNUM);
		send_token(s);
	}
	else if ((s = decode_linenum(event)) != NULL) {
		send_token(FEEDBACK_LINENUM);
		send_token(s);
	}
	else if (decode_end(event) && !loop) {
		send_token(FEEDBACK_SONGEND);
		return 1;
	}
	return 0;
}

void
send_sond_end() {
	send_token(FEEDBACK_SONGEND);
}

