#!/bin/sh

export PYTHONPATH=$PYTHONPATH:$(dirname "$0"):$HOME"/.virtualenvs/bg/lib/python2.7/site-packages"
gnubg -q -t -p ./main.py

