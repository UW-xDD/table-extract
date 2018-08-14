import math
import numpy as np
import itertools

from PIL import Image
from shapely.geometry import Polygon
from shapely.ops import cascaded_union

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from difflib import SequenceMatcher

def similar(a, b):
    return SequenceMatcher(None, a, b).ratio()

def similar_to_keyword(d):
    keywords = ['figure', 'fig', 'table', 'appendix', 'map']
    for word in keywords:
        if similar(d, word) > 0.6:
            return True

    return False

def clean_range(candidates):
    good_vals = []
    for idx, val in enumerate(candidates):
      if (idx == 0) or (idx == len(candidates)) or (idx != len(candidates) and idx != 0 and val <= int(candidates[(idx - 1)])*2):
        # cool
        good_vals.append(val)
      else:
        break

    complete = []
    for idx, val in enumerate(good_vals):
        if len(complete) == 0:
            complete.append(1)

        elif val > complete[-1] + 1:
            # Fill in the blanks
            for i in range(complete[-1] + 1, val + 1):
                complete.append(i)
        else:
            complete.append(val)

    return complete


def make_polygon(area):
    return Polygon([(area['x1'], area['y1']), (area['x1'], area['y2']), (area['x2'], area['y2']), (area['x2'], area['y1']), (area['x1'], area['y1'])])


def polygon_to_extract(polygon):
    bounds = polygon.bounds
    return {
        'x1': bounds[0],
        'y1': bounds[1],
        'x2': bounds[2],
        'y2': bounds[3]
    }


def union_extracts(extracts):
    unioned = cascaded_union([ make_polygon(p) for p in extracts ])

    if unioned.geom_type == 'Polygon':
        return [ polygon_to_extract(unioned) ]
    else:
        return [ polygon_to_extract(geom) for geom in unioned ]


def extract_table(doc, page, extract):
    image = Image.open('%s/png/page_%s.png' % (doc, page))
    image.crop((extract['x1'], extract['y1'], extract['x2'], extract['y2'])).save(doc + '/tables/page_' + str(page) + '_' + extract['name'].replace(' ', '_').replace('.', '') + '.png', 'png')


def enlarge_extract(extract, area):
    return {
        'x1': min([extract['x1'], area['x1']]),
        'y1': min([extract['y1'], area['y1']]),
        'x2': max([extract['x2'], area['x2']]),
        'y2': max([extract['y2'], area['y2']])
    }


def rectangles_intersect(a, b):
    # Determine whether or not two rectangles intersect
    if (a['x1'] < b['x2']) and (a['x2'] > b['x1']) and (a['y1'] < b['y2']) and (a['y2'] > b['y1']):
        return True
    else:
        return False


def extractbbox(title):
    # Given a tesseract title string, extract the bounding box coordinates
    for part in title.split(';'):
        if part.strip()[0:4] == 'bbox':
            bbox = part.replace('bbox', '').strip().split()
            return {
                'x1': int(bbox[0]),
                'y1': int(bbox[1]),
                'x2': int(bbox[2]),
                'y2': int(bbox[3])
            }
    return {}


def meanOfDifferences(d):
    return np.nanmean([abs(each[0] - each[1]) for each in  list(itertools.combinations(d, 2))])


def centroid(x):
    return {
        'x': x['x1'] + (float(x['x2'] - x['x1']) / 2),
        'y': x['y1'] + (float(x['y2'] - x['y1']) / 2)
    }


def min_distance(a, b):
    # Calculate 3 different distances and return the best one
    return min([ distance(a, b), top_left_distance(a, b), bottom_right_distance(a, b) ])

def top_left_distance(a, b):
    return abs(math.sqrt(math.pow((b['x1'] - a['x1']), 2) + math.pow((b['y1'] - a['y1']), 2)))

def bottom_right_distance(a, b):
    return abs(math.sqrt(math.pow((b['x2'] - a['x2']), 2) + math.pow((b['y2'] - a['y2']), 2)))

def distance(a, b):
    centroid_a = centroid(a)
    centroid_b = centroid(b)
    return abs(math.sqrt(math.pow((centroid_b['x'] - centroid_a['x']), 2) + math.pow((centroid_b['y'] - centroid_a['y']), 2)))

def get_gaps(x_axis):
    '''
    Presence of contiguous vertical white space is a good indicator that
    an area is a table. Given a list of 0s (white space) and 1s (content)
    returns a list of integers that correspond to contiguous pixels of
    whitespace.
    Ex: [1,1,1,1,0,0,0,0,0,0,1,1,0,0,0,0] -> [6, 4]
    '''
    gaps = []
    currentGap = 0
    for x in x_axis:
        if x == 1:
            if currentGap != 0:
                gaps.append(currentGap)
            currentGap = 0
        else:
            currentGap += 1

    return gaps


def expand_area(input_area, all_areas):
    text_blocks = [area for area in all_areas if area['type'] == 'text block']
    candidate_areas = [area for area in all_areas if area['type'] != 'text block' and area['type'] != 'decoration']

    extract = {
        'x1': input_area['x1'],
        'y1': input_area['y1'],
        'x2': input_area['x2'],
        'y2': input_area['y2']
    }

    for area in candidate_areas:
        # Create a geometry that is the current extract + the current area
        candidate_new_extract = enlarge_extract(extract, area)

        valid_extraction = True
        for block in text_blocks:
            will_intersect = rectangles_intersect(candidate_new_extract, block)
            if will_intersect:
                valid_extraction = False

        if valid_extraction:
            extract.update(candidate_new_extract)

    return extract

# Translated from the C++ implementation found here - http://www.geeksforgeeks.org/check-if-two-given-line-segments-intersect/
def lines_intersect(l1, l2):

    def on_segment(p1, p2, p3):
        if (
           (p2['x'] <= max([p1['x'], p3['x']])) and
           (p2['x'] >= min([p1['x'], p3['x']])) and
           (p2['y'] <= max([p1['y'], p3['y']])) and
           (p2['y'] >= min([p1['y'], p3['y']]))
         ):
            return True
        else:
            return False

    def orientation(p1, p2, p3):
        val = ((p2['y'] - p1['y']) * (p3['x'] - p2['x'])) - ((p2['x'] - p1['x']) * (p3['y'] - p2['y']))

        # colinear
        if val == 0:
            return 0
        # clockwise
        elif val > 0:
            return 1
        # counterclockwise
        else:
            return 2

    o1 = orientation({
        'x': l1['x1'],
        'y': l1['y1']
    }, {
        'x': l1['x2'],
        'y': l1['y2']
    }, {
        'x': l2['x1'],
        'y': l2['y1']
    })

    o2 = orientation({
        'x': l1['x1'],
        'y': l1['y1']
    }, {
        'x': l1['x2'],
        'y': l1['y2']
    }, {
        'x': l2['x2'],
        'y': l2['y2']
    })

    o3 = orientation({
        'x': l2['x1'],
        'y': l2['y1']
    }, {
        'x': l2['x2'],
        'y': l2['y2']
    }, {
        'x': l1['x1'],
        'y': l1['y1']
    })

    o4 = orientation({
        'x': l2['x1'],
        'y': l2['y1']
    }, {
        'x': l2['x2'],
        'y': l2['y2']
    }, {
        'x': l1['x2'],
        'y': l1['y2']
    })

    if o1 != o2 and o3 != o4:
        return True

    # Special cases
    if o1 == 0 and on_segment({
        'x': l1['x1'],
        'y': l1['y2']
    }, {
        'x': l2['x1'],
        'y': l2['y1']
    }, {
        'x': l1['x2'],
        'y': l1['y2']
    }):
        return True

    if o2 == 0 and on_segment({
        'x': l1['x1'],
        'y': l1['y1']
    }, {
        'x': l2['x2'],
        'y': l2['y2']
    }, {
        'x': l1['x2'],
        'y': l1['y2']
    }):
        return True

    if o3 == 0 and on_segment({
        'x': l2['x1'],
        'y': l2['y1']
    }, {
        'x': l1['x1'],
        'y': l1['y1']
    }, {
        'x': l2['x2'],
        'y': l2['y2']
    }):
        return True

    if o4 == 0 and on_segment({
        'x': l2['x1'],
        'y': l2['y1']
    }, {
        'x': l1['x2'],
        'y': l1['y2']
    }, {
        'x': l2['x2'],
        'y': l2['y2']
    }):
        return True

    return False

def get_header_footer(pages, page_height, page_width):
    header = { 'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0 }
    footer = { 'x1': 0, 'y1': 0, 'x2': 0, 'y2': 0 }

    # Find headers and footers (skip page 1 and pages that are abnormal orientations)
    page_areas = [  page['areas'] for i, page in enumerate(pages) if i != 0 and ((page['page']['y2'] - page['page']['y1']) == page_height) ]

    # Flatten
    areas = [area for areas in page_areas for area in areas]

    # Get words in areas that are not text blocks
    words = [ area['soup'].find_all('span', 'ocrx_word') for area in areas if area['type'] != 'text block'  ]

    # Get the dimensions of all areas identified as text blocks
    text_blocks = [ {'y1': area['y1'], 'y2': area['y2'], 'x1': area['x1'], 'x2': area['x2']} for area in areas if area['type'] == 'text block' ]
    # Maximum extent of text paragraphs in the document
    text_block_area = {
        'x1': min([ area['x1'] for area in text_blocks ]),
        'y1': min([ area['y1'] for area in text_blocks ]),
        'x2': max([ area['x2'] for area in text_blocks ]),
        'y2': max([ area['y2'] for area in text_blocks ])
    }

    # Get the bounding boxes of all words in the document that DO NOT belong to text blocks
    words_bboxes = []
    for word_a in words:
        for word in word_a:
            words_bboxes.append(extractbbox(word.get('title')))

    # Get the top-most coordinate of all word extents
    min_min_y1 = min([ word['y1'] for word in words_bboxes ])
    # For the words that have the top-most coordinate, get the mean of their y2
    max_min_y2 = np.nanmean([ word['y2'] for word in words_bboxes if word['y1'] == min_min_y1 ])

    # Get the max y1 of all word extents (looking for words in the last row of each page)
    min_max_y1 = max([ word['y1'] for word in words_bboxes ])
    # For the words that have the max y1, get the mean of their y2
    max_max_y2 = np.nanmean([ word['y2'] for word in words_bboxes if word['y1'] == min_max_y1 ])

    #
    # To determine if a document contains a header the following conditions must be met:
    #   + The middle of the vertical extent between the words in the top row must be on the top 1/4 of the page
    #   + The vertical extent of the words in the potential header must not overlap in y-space with any text block
    if (min_min_y1 + ((max_min_y2 - min_min_y1)/2)) < page_height/4 and not (text_block_area['y1'] <= max_min_y2 and min_min_y1 <= text_block_area['y2']):
        print 'HAS HEADER - ', min_min_y1, max_min_y2
        header = {
            'x1': 0,
            'y1': 0,
            'x2': page_width,
            'y2': int(max_min_y2)
        }

    # To determine if a footer is present, the same rules apply except it must be in the bottom 1/4 of the page
    if (min_max_y1 + ((max_max_y2 - min_max_y1)/2)) > (page_height - page_height/4) and not     (text_block_area['y1'] <= max_max_y2 and min_max_y1 <= text_block_area['y2']):
        print 'HAS FOOTER - ', min_max_y1, max_max_y2
        footer = {
            'x1': 0,
            'y1': min_max_y1,
            'x2': page_width,
            'y2': page_height
        }

    return header, footer


def buffer(area, amt):
    return {
        'x1': area['x1'] - amt,
        'y1': area['y1'] - amt,
        'x2': area['x2'] + amt,
        'y2': area['y2'] + amt
    }

def reclassify_areas(page_areas, line_height):
    buffered_areas = [ buffer(area, line_height) for area in page_areas ]
    relationships = {}

    for area_idx, area in enumerate(buffered_areas):
        relationships[area_idx] = [ { 'idx': i, 'geom': a } for i, a in enumerate(buffered_areas) if area_idx != i and rectangles_intersect(area, a) ]

    new_areas = []
    for area in relationships:
        part_of_existing = False
        # Check if it is part of an existing new area
        for i, new_area in enumerate(new_areas):
            if part_of_existing:
                continue

            if area in new_area['members']:
                part_of_existing = True
                # Append to this new area
                new_areas[i]['geom'] = enlarge_extract(new_areas[i]['geom'], buffered_areas[area])
                new_areas[i]['members'].add(area)
                for r in relationships[area]:
                    new_areas[i]['geom'] = enlarge_extract(new_areas[i]['geom'], r['geom'])
                    new_areas[i]['members'].add(r['idx'])

        if not part_of_existing:
            new_area = { 'x1': 9999999, 'y1': 9999999, 'x2': -9999999, 'y2': -9999999 }
            members = set([area])

            new_area = enlarge_extract(new_area, buffered_areas[area])
            for r in relationships[area]:
                new_area = enlarge_extract(new_area, r['geom'])
                members.add(r['idx'])

            new_areas.append({
                'members': members,
                'geom': new_area
            })

    return new_areas

def plot_new_areas(page_no, areas):
    fig = plt.figure()
    ax = fig.add_subplot(111, aspect='equal')

    #areas = [ makeBox(area) for area in area ]
#    words = [ makeBox(word) for word in words ]
    areas = [ area['geom'] for area in areas ]
    for area in areas:
        ax.add_patch(patches.Rectangle(
            (int(area['x1']), int(area['y1'])),
            int(area['x2']) - int(area['x1']),
            int(area['y2']) - int(area['y1']),
            fill=False,
            linewidth=0.5,
            edgecolor="#0000FF"
            )
            )


    # for word in words:
    #     ax.add_patch(patches.Rectangle(
    #         (int(word['x1']), int(word['y1'])),
    #         int(word['x2']) - int(word['x1']),
    #         int(word['y2']) - int(word['y1']),
    #         fill=False,
    #         linewidth=0.1,
    #         edgecolor="#000000"
    #         )
    #         )

    plt.ylim(0, 6600)
    plt.xlim(0, 5100)
    plt.axis("off")
    ax = plt.gca()
    ax.invert_yaxis()
    plt.axis('off')
    fig.savefig('./' + page_no + '.png', dpi=400, bbox_inches='tight', pad_inches=0)


def area_summary(area):
    summary = {}
    summary['soup'] = area
    # Bounding box (x1, y1, x2, y2)
    summary.update(extractbbox(area.get('title')))

    # Number of lines
    summary['lines'] = len(area.find_all('span', 'ocr_line'))
    summary['line_heights'] = []

    for line in area.find_all('span', 'ocr_line'):
        bbox = extractbbox(line.get('title'))
        height = bbox['y2'] - bbox['y1']
        summary['line_heights'].append(height)

    # Number of words
    summary['words'] = len(filter(None, area.getText().strip().replace('\n', ' ').replace('  ', ' ').split(' ')))

    # Area
    summary['area'] = (summary['x2'] - summary['x1']) * (summary['y2'] - summary['y1'])

    # Get spacing of words
    summary['x_gaps'] = np.zeros(summary['x2'] - summary['x1'], dtype=np.int)

    # Words per line
    summary['words_in_line'] = []
    summary['word_distances'] = []
    summary['word_heights'] = []
    summary['word_areas'] = []
    summary['words_per_line'] = []

    # Record the x position of the first word in each line
    summary['first_word_x'] = []

    # Iterate on each line in the area
    for line in area.find_all('span', 'ocr_line'):
        # For each line, get words
        words = line.find_all('span', 'ocrx_word')

        # Record the number of words in this line
        summary['words_per_line'].append(len(words))

        for word_idx, word in enumerate(words):
            wordbbox = extractbbox(word.get('title'))

            # Record the x coordinate of the first word of each line
            if word_idx == 0:
                summary['first_word_x'] = wordbbox['x1']

            summary['word_heights'].append(wordbbox['y2'] - wordbbox['y1'])
            summary['word_areas'].append((wordbbox['x2'] - wordbbox['x1']) * (wordbbox['y2'] - wordbbox['y1']))

            for x in range(wordbbox['x1'] - summary['x1'], wordbbox['x2'] - summary['x1']):
                summary['x_gaps'][x] = 1

            # If word isn't the last word in a line, get distance between word and word + 1
            if word_idx != (len(words) - 1):
                wordP1bbox = extractbbox(words[ word_idx + 1 ].get('title'))
                # Pythagorean theorum FTW
                summary['word_distances'].append(math.sqrt(math.pow((wordP1bbox['x1'] - wordbbox['x2']), 2) + math.pow((wordP1bbox['y1'] - wordbbox['y1']), 2)))

    # Count whitespace gaps
    summary['gaps'] = get_gaps(summary['x_gaps'])

    # Get the mean of the differences of the word distances (all the same == 0, difference increases away from 0)
    summary['word_separation_index'] = 0 if summary['words'] == 0 else meanOfDifferences(summary['word_distances'])

    # Quantify the variation in the height of words in this area
    summary['word_height_index'] = 0 if summary['words'] == 0 else meanOfDifferences(summary['word_heights'])

    # Get the average word height of this area
    summary['word_height_avg'] = 0 if summary['words'] == 0 else np.nanmean(summary['word_heights'])

    # Get word/area ratio
    summary['word_area_index'] = 0 if summary['words'] == 0 else np.sum(summary['word_areas']) / float(summary['area'])

    return summary

def summarize_document(area_stats):
    # Don't use areas with 1 line or no words in creating summary statistics
    return {
        'word_separation_mean': np.nanmean([np.nanmean(area['word_distances']) for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_separation_median': np.nanmedian([np.nanmean(area['word_distances']) for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_separation_std': np.nanstd([np.nanmean(area['word_distances'])for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_separation_index_mean': np.nanmean([area['word_separation_index'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_separation_index_median': np.nanmedian([area['word_separation_index'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_separation_index_std': np.nanstd([area['word_separation_index'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_height_index_mean': np.nanmean([area['word_height_index'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_height_index_median': np.nanmedian([area['word_height_index'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_height_index_std': np.nanstd([area['word_height_index'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_area_index_mean': np.nanmean([area['word_area_index'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_area_index_median': np.nanmedian([area['word_area_index'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_area_index_std': np.nanstd([area['word_area_index'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_height_avg': np.nanmean([area['word_height_avg'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_height_avg_median': np.nanmedian([area['word_height_avg'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),
        'word_height_avg_std': np.nanstd([area['word_height_avg'] for area in area_stats if area['words'] > 0 and area['lines'] > 1]),

        'line_height_avg': np.nanmean([a for a in area['line_heights'] for area in area_stats]),
        'line_height_std': np.nanstd([a for a in area['line_heights'] for area in area_stats])
    }
