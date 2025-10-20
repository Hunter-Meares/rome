########################################################################
# This is a main makefile for the "autoconf" bundle of SQLite. This is
# a trimmed-down version of the canonical makefile, devoid of most
# documentation. For the full docs, see /main.mk in the canonical
# source tree.
#
# Maintenance reminders:
#
# - To keep this working with an out-of-tree build, be sure to prefix
#   input file names with $(TOP)/ where appropriate (which is most
#   places).
#
# - The original/canonical recipes can be found in /main.mk in the
#   canonical source tree.
all:

TOP = /home/hunter/muddev/rome/sqlite-autoconf-3490100

PACKAGE_VERSION = 3.49.1

#
# Filename extensions for binaries and libraries
#
B.exe = 
T.exe = 
B.dll = .so
T.dll = .so
B.lib = .a
T.lib = .a

#
# Autotools-compatibility dirs
#
prefix      = /home/hunter/sqlite
datadir     = ${prefix}/share
mandir      = ${datadir}/man
includedir  = ${prefix}/include
exec_prefix = ${prefix}
bindir      = ${exec_prefix}/bin
libdir      = ${exec_prefix}/lib

#
# Required binaries
#
INSTALL = /usr/bin/install
AR = ar
AR.flags = cr
CC = cc


ENABLE_LIB_SHARED = 1
ENABLE_LIB_STATIC = 1

CFLAGS = -O2 -g 
#
# $(LDFLAGS.configure) represents any LDFLAGS=... the client passes to
# configure. See main.mk.
#
LDFLAGS.configure = 

CFLAGS.core = -fPIC
LDFLAGS.shlib = -shared
LDFLAGS.zlib = -lz
LDFLAGS.math = -lm
LDFLAGS.rpath = -Wl,-rpath,/home/hunter/sqlite/lib
LDFLAGS.pthread = -lpthread
LDFLAGS.dlopen = -ldl
LDFLAGS.readline = -lreadline -lncurses
CFLAGS.readline = -I/usr/include
LDFLAGS.rt = 
LDFLAGS.icu = 
CFLAGS.icu = 

# When cross-compiling, we need to avoid the -s flag because it only
# works on the build host's platform.
INSTALL.strip.1 = $(INSTALL)
INSTALL.strip.0 = $(INSTALL) -s
INSTALL.strip   = $(INSTALL.strip.0)
INSTALL.noexec  = $(INSTALL) -m 0644

install-dir.bin = $(DESTDIR)$(bindir)
install-dir.lib = $(DESTDIR)$(libdir)
install-dir.include = $(DESTDIR)$(includedir)
install-dir.pkgconfig = $(DESTDIR)$(libdir)/pkgconfig
install-dir.man1 = $(DESTDIR)$(mandir)/man1
install-dir.all = $(install-dir.bin) $(install-dir.include) \
  $(install-dir.lib) $(install-dir.man1) \
  $(install-dir.pkgconfig)
$(install-dir.all):
	@if [ ! -d "$@" ]; then set -x; $(INSTALL) -d "$@"; fi
# ^^^^ on some platforms, install -d fails if the target already exists.


#
# Vars with the AS_ prefix are specifically related to AutoSetup.
#
# AS_AUTO_DEF is the main configure script.
#
AS_AUTO_DEF = $(TOP)/auto.def

#
# Shell commands to re-run $(TOP)/configure with the same args it was
# invoked with to produce this makefile.
#
AS_AUTORECONFIG = cd /home/hunter/muddev/rome/sqlite-autoconf-3490100 && /home/hunter/muddev/rome/sqlite-autoconf-3490100/configure --prefix=/home/hunter/sqlite
Makefile: $(TOP)/Makefile.in $(AS_AUTO_DEF)
	$(AS_AUTORECONFIG)
	@touch $@

sqlite3.pc: $(TOP)/sqlite3.pc.in $(AS_AUTO_DEF)
	$(AS_AUTORECONFIG)
	@touch $@

sqlite_cfg.h: $(AS_AUTO_DEF)
	$(AS_AUTORECONFIG)
	@touch $@

#
# CFLAGS for sqlite3$(T.exe)
#
SHELL_OPT ?= -DHAVE_READLINE=1 -DSQLITE_HAVE_ZLIB=1

#
# Library-level feature flags
#
OPT_FEATURE_FLAGS = -DSQLITE_ENABLE_MATH_FUNCTIONS -DSQLITE_THREADSAFE=1

LDFLAGS.libsqlite3.soname = 
# soname: see https://sqlite.org/src/forumpost/5a3b44f510df8ded
LDFLAGS.libsqlite3.os-specific =  
# os-specific: see
# - https://sqlite.org/forum/forumpost/9dfd5b8fd525a5d7
# - https://sqlite.org/forum/forumpost/0c7fc097b2

LDFLAGS.libsqlite3 = \
  $(LDFLAGS.rpath) $(LDFLAGS.pthread) \
  $(LDFLAGS.math) $(LDFLAGS.dlopen) \
  $(LDFLAGS.zlib) $(LDFLAGS.icu) \
  $(LDFLAGS.rt) $(LDFLAGS.configure)
CFLAGS.libsqlite3 = -I. $(CFLAGS.core) $(CFLAGS.icu) $(OPT_FEATURE_FLAGS)

sqlite3.o: $(TOP)/sqlite3.h $(TOP)/sqlite3.c
	$(CC) -c $(TOP)/sqlite3.c -o $@ $(CFLAGS) $(CFLAGS.libsqlite3)

libsqlite3.LIB = libsqlite3$(T.lib)
libsqlite3.SO = libsqlite3$(T.dll)

$(libsqlite3.SO): sqlite3.o
	$(CC) -o $@  sqlite3.o $(LDFLAGS.shlib) \
		$(LDFLAGS) $(LDFLAGS.libsqlite3) \
		$(LDFLAGS.libsqlite3.os-specific) $(LDFLAGS.libsqlite3.soname)
all: $(libsqlite3.SO)

$(libsqlite3.LIB): sqlite3.o
	$(AR) $(AR.flags) $@ sqlite3.o
all: $(libsqlite3.LIB)

install-so-1: $(install-dir.lib) $(libsqlite3.SO)
	$(INSTALL) $(libsqlite3.SO) "$(install-dir.lib)"
	@if [ -f $(libsqlite3.SO).a ]; then \
		$(INSTALL) $(libsqlite3.SO).a "$(install-dir.lib)"; \
	fi
	@echo "Setting up $(libsqlite3.SO) version symlinks..."; \
	if [ x.dll = x$(T.dll) ]; then \
		echo "No library symlinks needed on this platform"; \
	elif [ x.dylib = x$(T.dll) ]; then \
		cd "$(install-dir.lib)" || exit $$?; \
		rm -f libsqlite3.0$(T.dll) libsqlite3.$(PACKAGE_VERSION)$(T.dll) || exit $$?; \
		dllname=libsqlite3.$(PACKAGE_VERSION)$(T.dll); \
		mv $(libsqlite3.SO) $$dllname || exit $$?; \
		ln -s $$dllname $(libsqlite3.SO) || exit $$?; \
		ln -s $$dllname libsqlite3.0$(T.dll) || exit $$?; \
		ls -la $$dllname $(libsqlite3.SO) libsqlite3.0$(T.dll); \
	else \
		cd "$(install-dir.lib)" || exit $$?; \
		rm -f $(libsqlite3.SO).0 $(libsqlite3.SO).$(PACKAGE_VERSION) || exit $$?; \
		mv $(libsqlite3.SO) $(libsqlite3.SO).$(PACKAGE_VERSION) || exit $$?; \
		ln -s $(libsqlite3.SO).$(PACKAGE_VERSION) $(libsqlite3.SO) || exit $$?; \
		ln -s $(libsqlite3.SO).$(PACKAGE_VERSION) $(libsqlite3.SO).0 || exit $$?; \
		ls -la $(libsqlite3.SO) $(libsqlite3.SO).[a03]*; \
		if [ -e $(libsqlite3.SO).0.8.6 ]; then \
			echo "ACHTUNG: legacy libtool-compatible install found. Re-linking it..."; \
			rm -f libsqlite3.la $(libsqlite3.SO).0.8.6 || exit $$?; \
			ln -s $(libsqlite3.SO).$(PACKAGE_VERSION) $(libsqlite3.SO).0.8.6 || exit $$?; \
			ls -la $(libsqlite3.SO).0.8.6; \
		elif [ x1 = "x$(INSTALL_SO_086_LINK)" ]; then \
			echo "ACHTUNG: installing legacy libtool-style links because INSTALL_SO_086_LINK=1"; \
			rm -f libsqlite3.la $(libsqlite3.SO).0.8.6 || exit $$?; \
			ln -s $(libsqlite3.SO).$(PACKAGE_VERSION) $(libsqlite3.SO).0.8.6 || exit $$?; \
			ls -la $(libsqlite3.SO).0.8.6; \
		fi; \
	fi

install-so-0 install-so-:
install-so: install-so-$(ENABLE_LIB_SHARED)
install: install-so

install-lib-1: $(install-dir.lib) $(libsqlite3.LIB)
	$(INSTALL.noexec) $(libsqlite3.LIB) "$(install-dir.lib)"
install-lib-0 install-lib-:
install-lib: install-lib-$(ENABLE_LIB_STATIC)
install: install-lib


# Flags to link the shell app either directly against sqlite3.c
# (ENABLE_STATIC_SHELL==1) or libsqlite3.so (ENABLE_STATIC_SHELL==0).
#
ENABLE_STATIC_SHELL = 1
sqlite3-shell-link-flags.1 = $(TOP)/sqlite3.c $(LDFLAGS.libsqlite3)
sqlite3-shell-link-flags.0 = -L. -lsqlite3 $(LDFLAGS.zlib)
sqlite3-shell-deps.1 = $(TOP)/sqlite3.c
sqlite3-shell-deps.0 = $(libsqlite3.SO)
sqlite3$(T.exe): $(TOP)/shell.c $(sqlite3-shell-deps.$(ENABLE_STATIC_SHELL))
	$(CC) -o $@ \
		$(TOP)/shell.c $(sqlite3-shell-link-flags.$(ENABLE_STATIC_SHELL)) \
		-I. $(OPT_FEATURE_FLAGS) $(SHELL_OPT) \
		$(CFLAGS) $(CFLAGS.readline) $(CFLAGS.icu) \
		$(LDFLAGS) $(LDFLAGS.readline)

all: sqlite3$(T.exe)

install-shell: sqlite3$(T.exe) $(install-dir.bin)
	$(INSTALL.strip) sqlite3$(T.exe) "$(install-dir.bin)"
install: install-shell

install-headers: $(TOP)/sqlite3.h $(install-dir.include)
	$(INSTALL.noexec) $(TOP)/sqlite3.h $(TOP)/sqlite3ext.h "$(install-dir.include)"
install: install-headers

install-pc: sqlite3.pc $(install-dir.pkgconfig)
	$(INSTALL.noexec) sqlite3.pc "$(install-dir.pkgconfig)"
install: install-pc

install-man1: $(TOP)/sqlite3.1 $(install-dir.man1)
	$(INSTALL.noexec) $(TOP)/sqlite3.1 "$(install-dir.man1)"
install: install-man1

clean:
	rm -f *.o sqlite3$(T.exe)
	rm -f $(libsqlite3.LIB) $(libsqlite3.SO) $(libsqlite3.SO).a

distclean: clean
	rm -f jimsh0$(T.exe) config.* sqlite3.pc sqlite_cfg.h Makefile

DIST_FILES := \
  README.txt VERSION \
  auto.def autosetup configure tea \
  sqlite3.h sqlite3.c shell.c sqlite3ext.h \
  Makefile.in Makefile.msc Makefile.fallback \
  sqlite3.rc sqlite3rc.h Replace.cs \
  sqlite3.pc.in sqlite3.1

# Maintenance note: dist_name must be sqlite-$(PACKAGE_VERSION) so
# that tool/mkautoconfamal.sh knows how to find it.
dist_name = sqlite-$(PACKAGE_VERSION)
dist_tarball = $(dist_name).tar.gz
dist:
	rm -fr $(dist_name)
	mkdir -p $(dist_name)
	cp -rp $(DIST_FILES) $(dist_name)/.
	rm -f $(dist_name)/tea/configure.ac.in
	tar czf $(dist_tarball) $(dist_name)
	rm -fr $(dist_name)
	ls -l $(dist_tarball)
