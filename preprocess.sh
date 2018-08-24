#! /bin/bash

if [ $# -lt 2 ]
  then echo -e "Please provide an output directory and an input PDF. Example: pdf2hocr ./ocrd ~/Downloads/document.pdf"
  exit 1
fi

mkdir -p $1
mkdir -p $1/png
mkdir -p $1/tesseract
mkdir -p $1/tesseract-txt
mkdir -p $1/ocr_annotations
mkdir -p $1/tables

gs -dBATCH -dNOPAUSE -sDEVICE=png16m -dGraphicsAlphaBits=4 -dTextAlphaBits=4 -r600 -sOutputFile="$1/png/page_%d.png" $2

cp $2 $1/orig.pdf
pdftotext $1/orig.pdf - -enc UTF-8 > $1/text.txt

ls $1/png | grep -o '[0-9]\+' | parallel -j 4 "./process.sh $1 {}"

tesseract_path="$1/tesseract-txt"
touch $1/plain_text.txt

for i in `seq 1 50`;
do
    if [ -f $tesseract_path/page_$i.txt ]
    then
        cat $tesseract_path/page_$i.txt >> $1/plain_text.txt
    fi
done
