@ECHO OFF

IF %1.==. (
    ECHO No parameter have been provided
    EXIT /b
) ELSE (
    ECHO Parameters:
    ECHO %1
)

MKDIR %1
MKDIR %1\png
MKDIR %1\tesseract
MKDIR %1\annotated
MKDIR %1\tables

gswin64c -dBATCH -dNOPAUSE -sDEVICE=png16m -dGraphicsAlphaBits=4 -dTextAlphaBits=4 -r600 -sOutputFile="%1/png/page_%%d.png" %2

COPY %2 %1\orig.pdf
pdftotext %1\orig.pdf - -enc UTF-8 > %1\text.txt

for /R "%1\png" %%f in (*.png) do (
    tesseract %1\png\%%~nf.png %1\tesseract\%%~nf.html hocr
    move %1\tesseract\%%~nf.html.hocr %1\tesseract\%%~nf.html
    python annotate.py %1/tesseract/%%~nf.html %1/annotated/%%~nf.png
)
