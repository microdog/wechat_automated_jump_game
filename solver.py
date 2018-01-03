import collections
import threading
import logging
import time
import os

import cv2 as cv
import numpy as np


class LRUCache(object):
    """Simple in-memory LRU cache."""

    def __init__(self, capacity):
        self.capacity = capacity
        self._cache = collections.OrderedDict()
        self._lock = threading.Lock()

    def get(self, key):
        with self._lock:
            try:
                value = self._cache.pop(key)
                self._cache[key] = value
                return value
            except KeyError:
                return None

    def set(self, key, value):
        with self._lock:
            try:
                self._cache.pop(key)
            except KeyError:
                pass
            self._cache[key] = value
            if len(self._cache) > self.capacity:
                self._cache.popitem(last=False)


class JumpGameSolver(object):
    TOP_KEEP_OUT_PX = 705
    BLUR_SIZE = (4, 4)

    logger = logging.getLogger('JumpGameSolver')

    def __init__(self, **kwargs):
        self.piece_template = None
        self.piece_template_screen_width = None

        self.results_path = kwargs.pop('results_path', None)

        piece_template_cache_size = kwargs.pop('piece_template_cache_size', 10)
        self.piece_template_cache = LRUCache(piece_template_cache_size)

    def load_piece_template(self, path, screen_width):
        self.piece_template = cv.imread(path)
        if self.piece_template is None:
            raise ValueError(
                'cannot load piece template from file {}'.format(path))
        self.piece_template_screen_width = int(screen_width)

    def find_piece(self, image, template, scale):
        """Find piece's center location (x, y)."""
        image = cv.blur(image, self.BLUR_SIZE)
        # Template alread blurred in get_piece_template()
        # template = cv.blur(template, (4, 4))

        res = cv.matchTemplate(image, template, cv.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

        self.logger.debug('Max value in piece matching: %s', max_val)

        if max_val < 0.6:
            return None

        return (max_loc[0] + int(50 * scale), max_loc[1] + int(161 * scale))

    def find_shape_points(self, image, piece_loc, sx, sy, scale):
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
            self.logger.info('Ignored shape: %s', (start_point, end_point))
            return None

        return (start_point, end_point)

    def find_board_center(self, image, piece_loc, scale):
        """Find target board's center location (x, y)."""
        image = cv.Canny(image, 50, 100)  # Edge detection
        w = image.shape[1]

        # Prevent the piece from being detected
        x_keepout = range(
            max(0, piece_loc[0] - int(50 * scale)),
            min(piece_loc[0] + int(51 * scale), w))

        shape_points = None
        for y in range(int(self.TOP_KEEP_OUT_PX * scale), piece_loc[1]):
            for x in range(w):
                if image[y, x] and x not in x_keepout:
                    shape_points = self.find_shape_points(
                        image, piece_loc, x, y, scale)
                    if shape_points:
                        break
            if shape_points:
                break

        if not shape_points:
            return None

        return (shape_points[0][0], shape_points[1][1])

    def calculate_distance(self, image, template, scale):
        """Calculate distance."""
        piece_loc = self.find_piece(image, template, scale)
        self.logger.debug('Piece location: %s', piece_loc)

        if not piece_loc:
            return None

        board_center = self.find_board_center(image, piece_loc, scale)
        self.logger.debug('Board center location: %s', board_center)

        if not board_center:
            return None

        if self.results_path is not None:
            cv.rectangle(image, piece_loc, piece_loc, (255, 0, 0), 1)
            cv.rectangle(image, board_center, board_center, (255, 0, 0), 1)
            filename = '{}.png'.format(int(time.time()))
            cv.imwrite(os.path.join(self.results_path, filename), image)

        return cv.norm(piece_loc, board_center)

    def calculate_time(self, distance, image, scale):
        """Map distance to time in ms."""
        return int(
            1.0 * distance / scale * 1440 / self.piece_template_screen_width)

    def get_piece_template(self, scale):
        template = self.piece_template_cache.get(scale)
        if template is None:
            self.logger.debug('Creating resized template: %s', scale)
            template = cv.resize(
                self.piece_template, (0, 0),
                fx=scale,
                fy=scale,
                interpolation=cv.INTER_NEAREST)
            template = cv.blur(template, self.BLUR_SIZE)
            self.piece_template_cache.set(scale, template)
        else:
            self.logger.debug('Cached template used: %s', scale)
        return template

    def solve_image(self, image):
        scale = 1.0 * image.shape[1] / self.piece_template_screen_width

        template = self.get_piece_template(scale)

        distance = self.calculate_distance(image, template, scale)
        if distance is None:
            return None
            self.logger.debug('Jump target not found in image')
        self.logger.debug('Distance: %s', distance)

        press_time = self.calculate_time(distance, image, scale)
        self.logger.debug('Press time: %s', press_time)

        return press_time

    def solve_from_stream(self, stream):
        buf = np.fromstring(stream.read(), np.uint8)
        if not buf.size:
            raise ValueError('missing image data')

        image = cv.imdecode(buf, cv.IMREAD_COLOR)
        if image is None:
            raise ValueError('invalid image data')

        del buf

        return self.solve_image(image)


__all__ = ['JumpGameSolver']
