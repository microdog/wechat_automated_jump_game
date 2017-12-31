from __future__ import print_function

import time
import argparse

import cv2 as cv
import numpy as np
from flask import Flask, request, abort

TOP_KEEPOUT_PX = 400

save_results = False
piece_template = None
piece_template_screen_width = None
app = Flask(__name__)


def load_piece_template(path, screen_width):
    global piece_template, piece_template_screen_width
    piece_template = cv.imread(path)
    piece_template_screen_width = screen_width


def find_piece(image, template, scale):
    """Find piece's center location (x, y)."""
    image = cv.blur(image, (4, 4))
    template = cv.blur(template, (4, 4))

    res = cv.matchTemplate(image, template, cv.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

    if max_val < 0.6:
        return None

    return (max_loc[0] + int(50 * scale), max_loc[1] + int(161 * scale))


def find_shape_points(image, piece_loc, sx, sy, scale):
    """Find a shape's top-center and right-most points ((x, y), (x, y))."""
    start_point = [0, sy]

    # Find start point
    h, w = image.shape[:2]
    for x in range(sx, w):
        if image[sy, x]:
            start_point[0] = x
        else:
            break

    end_point = list(start_point)
    start_point[0] = (start_point[0] + sx) / 2

    # Find end point
    vp = 0  # Vertical pixels
    for y in range(sy + 1, piece_loc[1]):
        new_x = end_point[0]
        for x in range(new_x, w):
            if image[y, x] and (x + 1 == w or not image[y, x + 1]):
                new_x = x
                break
        if new_x == end_point[0]:  # Vertical pixel
            vp += 1
            if vp >= 4:
                break
        elif new_x < end_point[0]:  # Corner
            break
        else:
            vp = 0
            end_point[0] = new_x
            end_point[1] = y

    # Try to ignore musical note
    if end_point[1] - start_point[1] < int(20 * scale):
        print('Ignored shape: ', (start_point, end_point))
        return None

    return (start_point, end_point)


def find_board_center(image, piece_loc, scale):
    """Find target board's center location (x, y)."""
    image = cv.Canny(image, 10, 20)  # Edge detection
    w = image.shape[1]

    # Prevent the piece from being detected
    x_keepout = range(
        max(0, piece_loc[0] - int(50 * scale)),
        min(piece_loc[0] + int(51 * scale), w))

    shape_points = None
    for y in range(int(TOP_KEEPOUT_PX * scale), piece_loc[1]):
        for x in range(w):
            if image[y, x] and x not in x_keepout:
                shape_points = find_shape_points(image, piece_loc, x, y, scale)
                if shape_points:
                    break
        if shape_points:
            break

    if not shape_points:
        return None

    return (shape_points[0][0], shape_points[1][1])


def calculate_distance(image, template, scale):
    """Calculate distance."""
    piece_loc = find_piece(image, template, scale)
    print('Piece: ', piece_loc)

    if not piece_loc:
        return None

    board_center = find_board_center(image, piece_loc, scale)
    print('Board center: ', board_center)

    if not board_center:
        return None

    if save_results:
        cv.rectangle(image, piece_loc, piece_loc, (255, 0, 0), 1)
        cv.rectangle(image, board_center, board_center, (255, 0, 0), 1)
        cv.imwrite('{}.png'.format(time.time()), image)

    return cv.norm(piece_loc, board_center)


def calculate_time(distance, image, scale):
    """Map distance to time in ms."""
    return int(1.0 * distance / scale * 1440 / piece_template_screen_width)


@app.route('/', methods=['POST'])
def handler():
    buf = np.fromstring(request.data, np.uint8)
    image = cv.imdecode(buf, cv.IMREAD_COLOR)

    if image.shape[1] != piece_template.shape[1]:
        scale = 1.0 * image.shape[1] / piece_template_screen_width
        # TODO cache resized template
        template = cv.resize(
            piece_template, (0, 0),
            fx=scale,
            fy=scale,
            interpolation=cv.INTER_NEAREST)
    else:
        scale = 1.0
        template = piece_template

    distance = calculate_distance(image, template, scale)
    print('Distance: ', distance)

    if distance is None:
        abort(400)

    press_time = calculate_time(distance, image, scale)
    print('Press time: ', press_time)

    return str(press_time)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Automated WeChat jump game server')
    parser.add_argument(
        '--piece-template',
        type=str,
        default='piece.png',
        help='path to piece template image (default: piece.png)')
    parser.add_argument(
        '--piece-template-screen-width',
        type=int,
        default=1440,
        help='screen width of piece template image (default: 1440)')
    parser.add_argument(
        '--debug', action='store_true', help='enable flask debug mode')
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='http listen host (default: 127.0.0.1)')
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='http listen port (default: 5000)')
    parser.add_argument(
        '--save-results', action='store_true', help='save images')

    args = parser.parse_args()

    save_results = args.save_results
    load_piece_template(args.piece_template, args.piece_template_screen_width)
    app.run(debug=args.debug, host=args.host, port=args.port)
