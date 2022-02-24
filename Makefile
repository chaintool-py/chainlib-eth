PREFIX ?= /usr/local
BUILD_DIR = build/$(PREFIX)/share/man

man:
	mkdir -vp $(BUILD_DIR)
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py gas` -v -n eth-gas -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py info` -v -n eth-info -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py get` -v -n eth-get -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py decode` -v -n eth-decode -d $(BUILD_DIR)/ man

.PHONY: man
