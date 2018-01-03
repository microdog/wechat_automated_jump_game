import collections
import logging
import os
import threading
import time

import cv2 as cv
import numpy as np

try:
    import solver_cython as c
except ImportError:
    import solver_python as c

logger = logging.getLogger('JumpGameSolver')


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


class SolverException(Exception):
    pass


class SolverInputException(SolverException):
    pass


class JumpGameSolver(object):
    TOP_KEEP_OUT_PX = 705
    BLUR_SIZE = (4, 4)

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
        return c.find_piece(image, template, scale, self.BLUR_SIZE, logger)

    def find_board_center(self, image, piece_loc, scale):
        """Find target board's center location (x, y)."""
        return c.find_board_center(image, piece_loc, scale, self.TOP_KEEP_OUT_PX, logger)

    def calculate_distance(self, image, template, scale):
        """Calculate distance."""
        piece_loc = self.find_piece(image, template, scale)
        logger.debug('Piece location: %s', piece_loc)

        if not piece_loc:
            return None

        board_center = self.find_board_center(image, piece_loc, scale)
        logger.debug('Board center location: %s', board_center)

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
        return int(1.0 * distance / scale * 1440 / self.piece_template_screen_width)

    def get_piece_template(self, scale):
        template = self.piece_template_cache.get(scale)
        if template is None:
            logger.debug('Creating resized template: %s', scale)
            template = cv.resize(
                self.piece_template, (0, 0),
                fx=scale,
                fy=scale,
                interpolation=cv.INTER_NEAREST)
            template = cv.blur(template, self.BLUR_SIZE)
            self.piece_template_cache.set(scale, template)
        else:
            logger.debug('Cached template used: %s', scale)
        return template

    def solve_image(self, image):
        scale = 1.0 * image.shape[1] / self.piece_template_screen_width

        template = self.get_piece_template(scale)

        distance = self.calculate_distance(image, template, scale)
        if distance is None:
            logger.debug('Jump target not found in image')
            return None
        logger.debug('Distance: %s', distance)

        press_time = self.calculate_time(distance, image, scale)
        logger.debug('Press time: %s', press_time)

        return press_time

    def solve_from_stream(self, stream):
        buf = np.fromstring(stream.read(), np.uint8)
        if not buf.size:
            raise SolverInputException('missing image data')

        image = cv.imdecode(buf, cv.IMREAD_COLOR)
        if image is None:
            raise SolverInputException('invalid image data')

        del buf

        return self.solve_image(image)


__all__ = ['JumpGameSolver', 'SolverException', 'SolverInputException']
