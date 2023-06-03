PACKAGE=chainlib-eth
PREFIX ?= /usr/local
BUILD_DIR = man/build/

man:
	mkdir -vp $(BUILD_DIR)
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py gas` -v -n eth-gas -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py info` -v -n eth-info -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py get` -v -n eth-get -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py decode` -v -n eth-decode -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py encode` -v -n eth-encode -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py count` -v -n eth-count -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py raw` -v -n eth-raw -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py wait` -v -n eth-wait -d $(BUILD_DIR)/ man
	chainlib-man.py -b `PYTHONPATH=. python chainlib/eth/runnable/flags.py balance` -v -n eth-balance -d $(BUILD_DIR)/ man

.PHONY: man

build:
	python setup.py bdist_wheel

.PHONY clean:
	rm -rf build
	rm -rf dist
	rm -rf $(PACKAGE).egg-info

readme:
	make -C doc/texinfo readme
	pandoc -f docbook -t gfm doc/texinfo/build/docbook.xml > README.md

python: build

doc:
	make -C doc/texinfo

