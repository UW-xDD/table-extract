#!/usr/bin/env bash

if [ $# -lt 2 ]
  then echo -e "Please provide an output directory and an input PDF. Example: pdf2hocr ./ocrd ~/Downloads/document.pdf"
  exit 1
fi

# Preprocess the pdf using tesseract.
./preprocess.sh $1 $2

# Autodetect tables.
python do_extract.py $1