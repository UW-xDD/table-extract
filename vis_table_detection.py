import matplotlib.pyplot as plt
import matplotlib.patches as patches


def make_box(bbox):
    return {
        '_left': int(bbox['x1']),
        '_top': int(bbox['y1']),
        '_right': int(bbox['x2']),
        '_bottom': int(bbox['y2']),
        'width': int(bbox['x2']) - int(bbox['x1']),
        'height': int(bbox['y2']) - int(bbox['y1'])
    }


def make_rectangle(area):
    box = make_box(area)
    color = get_color_code(area['type'])
    rect = patches.Rectangle(
            (box['_left'], box['_top']),
            box['_right'] - box['_left'],
            box['_bottom'] - box['_top'],
            fill=False,
            linewidth=0.4,
            edgecolor=color
    )
    return rect


def get_color_code(area_type):
    return {
        'table': "#282a2e",
        'text block': "#ff0000",
        'decoration': "#282a2e",
        'caption': "#282a2e",
        'line': "#282a2e",
        'other': "#282a2e"
    }[area_type]


def plot_table_detection(pages, path):
    for page in pages:
        plot_table_detection_per_page(page, path)


def plot_table_detection_per_page(page, path, out_dir='table-detection'):
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')

    for area in page['areas']:
        ax.add_patch(make_rectangle(area))

    bbox_page = make_box(page['page'])
    plt.ylim(0, bbox_page['_bottom'])
    plt.xlim(0, bbox_page['_right'])
    plt.axis("off")
    ax = plt.gca()
    ax.invert_yaxis()
    plt.axis('off')
    outfile = path + "/" + out_dir + "/page_" + page['page_no'] + ".png"
    fig.savefig(outfile, dpi=400, bbox_inches='tight', pad_inches=0)
