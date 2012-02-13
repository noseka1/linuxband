#                                               -*- Autoconf -*-
# Process this file with autoconf to produce a configure script.

AC_PREREQ(2.65)
AC_INIT([linuxband], [12.02.1], [ales.nosek@gmail.com], [linuxband], [http://linuxband.org])
AC_CONFIG_SRCDIR([src/main/c/linuxband-player.c])
AC_CONFIG_HEADER([config.h])

# Checks for programs.
AC_PROG_CC
AC_PROG_INSTALL

# Checks for header files.
AC_HEADER_STDC
AC_CHECK_HEADERS([stdlib.h string.h sys/time.h unistd.h])

# Checks for typedefs, structures, and compiler characteristics.
AC_C_CONST
AC_TYPE_INT8_T
AC_HEADER_TIME
AC_TYPE_UINT16_T
AC_TYPE_UINT32_T
AC_C_VOLATILE

# Checks for library functions.
AC_FUNC_MALLOC
AC_FUNC_MEMCMP
AC_FUNC_REALLOC
AC_TYPE_SIGNAL
AC_FUNC_STRTOD
AC_CHECK_FUNCS([gettimeofday memset pow strdup strerror strtol])

PKG_CHECK_MODULES(GLIB, glib-2.0 >= 2.2)
AC_SUBST(GLIB_CFLAGS)
AC_SUBST(GLIB_LIBS)

PKG_CHECK_MODULES(GTHREAD, gthread-2.0 >= 2.2)
AC_SUBST(GTHREAD_CFLAGS)
AC_SUBST(GTHREAD_LIBS)

PKG_CHECK_MODULES(JACK, jack >= 0.102.0)
AC_SUBST(JACK_CFLAGS)
AC_SUBST(JACK_LIBS)

PKG_CHECK_MODULES(SMF, smf >= 1.3)
AC_SUBST(SMF_CFLAGS)
AC_SUBST(SMF_LIBS)

PKG_CHECK_MODULES(JACK_MIDI_NEEDS_NFRAMES, jack < 0.105.00,
	AC_DEFINE(JACK_MIDI_NEEDS_NFRAMES, 1, [whether or not JACK routines need nframes parameter]), true)

#AC_ARG_WITH([lash],
#	    [AS_HELP_STRING([--with-lash],
#	    [support LASH @<:@default=check@:>@])],
#	    [],
#	    [with_lash=check])

#AS_IF([test "x$with_lash" != xno],
#      [PKG_CHECK_MODULES(LASH, lash-1.0, AC_DEFINE([HAVE_LASH], [], [Defined if we have LASH support.]),
#      [if test "x$with_lash" != xcheck; then
#       AC_MSG_FAILURE([--with-lash was given, but LASH was not found])
#       fi
#       ])])

#AC_SUBST(LASH_CFLAGS)
#AC_SUBST(LASH_LIBS)

# Additional install locations
pkgdatadir=${datadir}/${PACKAGE_NAME}
pkglibdir=${libdir}/${PACKAGE_NAME}
AC_SUBST(pkgdatadir)
AC_SUBST(pkglibdir)

AC_CONFIG_FILES([Makefile])
AC_OUTPUT
