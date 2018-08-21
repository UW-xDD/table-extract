# tesseract-tables
A tool for extracting tables, figures, maps, and pictures from PDFs using Tesseract

## Installation
If you are using MacOS you can install the dependencies as so:

````
brew install ghostscript parallel tesseract
````

Note: Linux users may need to install the Tcl/Tk interface. On Ubuntu:

```
sudo apt install python-tk
```

Next, install the Python dependencies:

````
pip install -r requirements.txt
````

## Example usage
Assuming you have a document named `my_doc.pdf`, you can prepare it for processing and extract tables as so:

````bash
./preprocess.sh ./my_doc_processed ./my_doc.pdf
python do_extract.py ./my_doc_processed
````

This will extract tables and figures to `./my_doc_processed/tables`. The first command will parse the PDF into the necessary directory structure and create the necessary data products for Tesseract. The second will extract tables.

## preprocess.sh
Script for prepping a PDF for table extraction. Converts each page of the PDF to a PNG with Ghostscript, then runs the PNGs through Tesseract. Also runs each page through `annotate.py` to assist in debugging. Assumes local installation of [tesseract-ocr](https://github.com/tesseract-ocr/tesseract).

#### Example usage

````
./preprocess.sh ./my_document_processed my_document.pdf
````

This creates the file structure necessary for extraction:
````
document_name
  annotated (pngs of what tesseract sees)
  png (each page of the PDF as a PNG image)
  tables (extractions)
  tesseract (HTML for each page produced by tesseract)
  orig.pdf (The original document)
  text.txt (The extracted text layer)
````

## Funding
Development supported by NSF ICER 1343760

## License
MIT
