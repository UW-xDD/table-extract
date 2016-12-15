# tesseract-tables
A tool for extracting tables, figures, maps, and pictures from PDFs using Tesseract

## pdf2hocr
Script for prepping a PDF for table extraction. Converts each page of the PDF to a PNG with Ghostscript, then runs the PNGs through Tesseract. Also runs each page through `annotate.py` to assist in debugging.

#### Example usage

````
pdf2hocr ./my_document_processed my_document.pdf
````


## do_extract.py
Script for processing the output of `pdf2hocr`.

#### Example usage

````
python do_extract.py ~/Documents/doc
````

## annotate.py
Creates a PNG that shows the areas of a page identified by Tesseract. Useful for debugging.

## helpers.py
Various functions for processing tables.

## table_extractor.py
Entry script to table extraction.

#### extract_tables(document_path)
Process a document for tables. Pass it a path to a document that has been pre-processed with pdf2hocr
