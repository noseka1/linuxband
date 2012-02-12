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
#ifndef JACKSMFPLAYERRC_H_
#define JACKSMFPLAYERRC_H_

void
remote_control_start(char *pipe_name);

double
loop_song(smf_t *smf);

int
loop_seek(smf_t *smf, double pos);

int
process_meta_event(char *event);

void
jack_shutdown(void *arg);

void
send_sond_end();

extern pthread_mutex_t mutex;

#endif /* JACKSMFPLAYERRC_H_ */
