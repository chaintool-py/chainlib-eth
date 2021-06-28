#!/bin/bash

set -e
set -x
#export PYTHONPATH=${PYTHONPATH:.}
for f in `ls tests/*.py`; do
	python $f
done
set +x
set +e
