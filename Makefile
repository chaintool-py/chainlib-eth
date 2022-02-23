PREFIX ?= /usr/local
BUILD_DIR = build/$(PREFIX)/share/man

man:
	mkdir -vp $(BUILD_DIR)
	chainlib-man.py -b`PYTHONPATH=. python chainlib/eth/runnable/flags.py gas` -n eth-gas -d $(BUILD_DIR)/ man/gas.head.groff
	chainlib-man.py -b`PYTHONPATH=. python chainlib/eth/runnable/flags.py info` -n eth-info -d $(BUILD_DIR)/ man/info.head.groff


.PHONY: man
