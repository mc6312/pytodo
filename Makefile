packer = 7z
pack = $(packer) a -mx=9
arcx = .7z
docs = COPYING Changelog README.md
basename = pytodo
srcversion = pytodo
version = $(shell python3 -c 'from $(srcversion) import VERSION; print(VERSION)')
branch = $(shell git symbolic-ref --short HEAD)
title_version = $(shell python3 -c 'from $(srcversion) import TITLE_VERSION; print(TITLE_VERSION)')
zipname = $(basename).zip
arcname = $(basename)$(arcx)
srcarcname = $(basename)-$(branch)-src$(arcx)
srcs = *.py
backupdir = ~/shareddocs/pgm/python/

#app:
#	$(pack) -tzip $(zipname) $(srcs)
#	@echo '#!/usr/bin/env python3' >$(basename)
#	@cat $(zipname) >>$(basename)
#	rm $(zipname)
#	chmod 755 $(basename)

archive:
	$(pack) $(srcarcname) *.py *. Makefile *.geany $(docs)
distrib:
	make app
	$(eval distname = $(basename)-$(version)$(arcx))
	$(pack) $(distname) $(basename) $(docs)
	mv $(distname) ~/downloads/
backup:
	make archive
	mv $(srcarcname) $(backupdir)
update:
	$(packer) x -y $(backupdir)$(srcarcname)
commit:
	make todo
	git commit -a -uno -m "$(version)"
docview:
	$(eval docname = README.htm)
	@echo "<html><head><meta charset="utf-8"><title>$(title_version) README</title></head><body>" >$(docname)
	markdown_py README.md >>$(docname)
	@echo "</body></html>" >>$(docname)
	x-www-browser $(docname)
	#rm $(docname)
show-branch:
	@echo "$(branch)-$(version)"
todo:
	$(basename).py $(basename).py >TODO
