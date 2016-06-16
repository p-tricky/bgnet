#!/bin/sh

export PYTHONPATH=$PYTHONPATH:$(dirname "$0")
gnubg -q -t -p ./main.py

