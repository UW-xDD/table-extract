import sys
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def make_box(bbox):
    if isinstance(bbox, list):
        return {
            '_left': int(bbox[0]),
            '_top': int(bbox[1]),
            '_right': int(bbox[2]),
            '_bottom': int(bbox[3]),
            'width': int(bbox[2]) - int(bbox[0]),
            'height': int(bbox[3]) - int(bbox[1])
        }
    elif isinstance(bbox, dict):
        return {
            '_left': int(bbox['x1']),
            '_top': int(bbox['y1']),
            '_right': int(bbox['x2']),
            '_bottom': int(bbox['y2']),
            'width': int(bbox['x2']) - int(bbox['x1']),
            'height': int(bbox['y2']) - int(bbox['y1'])
        }
    else:
        raise RuntimeError("Type: {} is not support in this function".format(
            type(bbox)))


def get_bbox(title):
    title_parts = title.split(';')
    for part in title_parts:
        if part.strip()[0:4] == 'bbox':
            return part.replace('bbox', '').strip().split()

    return


def tess(infile, outfile):
    with open(infile) as hocr:
        text = hocr.read()

    soup = BeautifulSoup(text, "html.parser")
    pages = soup.find_all('div', 'ocr_page')
    careas = soup.find_all('div', 'ocr_carea')
    #pars = soup.find_all('p', 'ocr_par')
    words = soup.find_all('span', 'ocrx_word')

    page_boxes = [make_box(get_bbox(page.get('title'))) for page in pages]
    carea_boxes = [make_box(get_bbox(carea.get('title'))) for carea in careas]
    #par_boxes = [makeBox(getbbox(par.get('title'))) for par in pars]
    word_boxes = [make_box(get_bbox(word.get('title'))) for word in words]

    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')

    for box in page_boxes:
        ax.add_patch(patches.Rectangle(
            (box['_left'], box['_top']),
            box['_right'] - box['_left'],
            box['_bottom'] - box['_top'],
            fill=False,
            linewidth=0.2,
            edgecolor="#1d1f21"
        )
        )

    for box in carea_boxes:
        ax.add_patch(patches.Rectangle(
            (box['_left'], box['_top']),
            box['_right'] - box['_left'],
            box['_bottom'] - box['_top'],
            fill=False,
            linewidth=0.5,
            edgecolor="#282a2e"
            )
            )

    for box in word_boxes:
        ax.add_patch(patches.Rectangle(
            (box['_left'], box['_top']),
            box['_right'] - box['_left'],
            box['_bottom'] - box['_top'],
            fill=False,
            linewidth=0.1,
            edgecolor="#373b41"
            )
            )

    plt.ylim(0,page_boxes[0]['_bottom'])
    plt.xlim(0,page_boxes[0]['_right'])
    plt.axis("off")
    ax = plt.gca()
    ax.invert_yaxis()
    plt.axis('off')
    fig.savefig(outfile, dpi=400, bbox_inches='tight', pad_inches=0)


def make_rectangle(area):
    box = make_box(area)
    color = get_color_code(area['type'])
    rect = patches.Rectangle(
            (box['_left'], box['_top']),
            box['width'],
            box['height'],
            fill=False,
            linewidth=0.4,
            edgecolor=color
    )
    return rect


def get_color_code(area_type):
    return {
        'table': "#912226", # red
        'text block': "#969896", # gray
        'decoration': "#1d2594", # blue
        'caption': "#778900", # green
        'line': "#1d1f21", # black
        'other': "#ae7b00" # orange
    }[area_type]


def plot_table_detection(pages, path):
    for page in pages:
        plot_table_detection_per_page(page, path)


def plot_table_detection_per_page(page, path, overlay=True, out_dir='table-detection'):
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')

    areas = page['areas']

    for area in areas:
        ax.add_patch(make_rectangle(area))

    plot_table_scores(ax, areas)

    bbox_page = make_box(page['page'])
    plt.ylim(0, bbox_page['_bottom'])
    plt.xlim(0, bbox_page['_right'])
    plt.axis("off")
    ax = plt.gca()
    ax.invert_yaxis()
    if overlay:
        img = plt.imread(path + "/png/page_" + page['page_no'] + ".png")
        ax.imshow(img)
    plt.axis('off')
    outfile = path + "/" + out_dir + "/page_" + page['page_no'] + ".png"
    fig.savefig(outfile, dpi=600, bbox_inches='tight', pad_inches=0)


def plot_table_scores(plot, areas):
    for area in areas:
        box = make_box(area)
        color = get_color_code(area['type'])
        table_score_str = "ts:{}".format(area['table_score'])
        plot.text(box['_left'] + 0.5 * box['width'], box['_top'] + 0.5 * box['height'], table_score_str,
                  horizontalalignment='center',
                  verticalalignment='center',
                  color=color,
                  fontsize=8,
                  alpha=0.6)


if len(sys.argv) == 3:
    tess(sys.argv[1], sys.argv[2])
else:
    print 'Script requires two parameters: an input Tesseract HOCR file and an output file name and location'
