#!/usr/bin/env bash


if [ $# -lt 1 ]
  then echo -e "Please provide an input directory."
  exit 1
fi

# Autodetect tables.
python do_extract.py $1