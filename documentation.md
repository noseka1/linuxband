---
layout: page
title: "Documentation"
group: navigation
order: 2
---
{% include JB/setup %}
<a href="http://linuxaudio.org"><img style="float:right" src="/assets/images/lao_compact_06_trans_w100.png" /></a>

## Requirements
Following are the requirements for build and runtime:

*  MMA (Musical MIDI Accompaniment)<br />
<http://www.mellowood.ca/mma>
*  JACK Audio Connection Kit<br />
<http://http://jackaudio.org>
*  Standard MIDI File format library<br />
<http://sourceforge.net/projects/libsmf>
*  Python >= 2.5 <br />
<http://python.org>
*  PyGTK: GTK+ for Python<br />
<http://www.pygtk.org>
*  GtkSourceView 2.x and Python bindings<br />
<http://projects.gnome.org/gtksourceview><br />
<http://projects.gnome.org/gtksourceview/pygtksourceview.html>

On Debian you can install the dependencies by typing (as root):<br />
`apt-get install libjack-dev`<br />
`apt-get install libsmf-dev`<br />
`apt-get install python-gtk2`<br />
`apt-get install python-gtksourceview2`<br />

You can download the Debian package for MMA <a href="http://www.mellowood.ca/mma/downloads.html">here</a>.

## Optional Downloads
Optionally, you can install a GUI front-end for JACK audio server:

*  QJackCtl<br />
<http://qjackctl.sourceforge.net>

Optionally, to play MIDI, download a software synthesizer and sound fonts:<br />

*  FluidSynth real-time software synthesizer<br />
<http://sourceforge.net/apps/trac/fluidsynth>
*  Fluidsynth GUI front-end<br />
<http://qsynth.sourceforge.net>
* Fluid sound font<br />
<http://soundfonts.homemusician.net/collections_soundfonts/fluid_release_3.html>

## Installation
Download the latest LinuxBand source code tarball from <a href="downloads.html">Downloads section</a>.<br />
To compile LinuxBand, run following commands in the extracted directory:<br />
`./configure`<br />
`make`<br />
You can type `./configure --help` to see a list of compilation options. After LinuxBand is compiled run:<br />
`make install`<br />
as root to install it.

## Get Involved
LinuxBand is free software and contributions are very welcome.

*  Submit the bugreports or suggestions on the GitHub bug tracker <a href="https://github.com/noseka1/linuxband/issues">here</a>.
*  If you are a programmer, fork the <a href="https://github.com/noseka1/linuxband">LinuxBand project</a> on GitHub, make changes and send us a pull request. Or send your patches per email.
   The Python code holds the style guidelines suggested by <a href="http://google-styleguide.googlecode.com/svn/trunk/pyguide.html">Google Python Style Guide</a>.
*  If you want to contribute documentation or changes to this website, fork the <a href="https://github.com/noseka1/linuxband/tree/gh-pages">LinuxBand project</a>, make changes on  gh-pages branch and send us a pull request. You can always send your changes or suggestions per email.

## Contact
Send your comments and suggestions to Aleš Nosek, <a href="mailto:ales.nosek@gmail.com">ales.nosek@gmail.com</a>
