import argparse
import random
import logging

from flask import Flask, request, abort
from solver import JumpGameSolver

app = Flask(__name__)
app.config.from_object('server_config')

solver = None


@app.route('/', methods=['POST'], strict_slashes=False)
def handler():
    try:
        press_time = solver.solve_from_stream(request.stream)
    except ValueError as e:
        abort(400, e.message)

    if press_time is None:
        abort(400, 'jump target not found in image')

    try:
        jitter = request.args.get('jitter', None, float)
    except ValueError:
        abort(400, 'invalid jitter value')

    if jitter is not None:
        app.logger.debug('Applying jitter: %s', jitter)
        press_time = int(
            float(press_time) * random.uniform(1 - jitter, 1 + jitter))
        app.logger.debug('Actual press time: %s', press_time)

    return str(press_time)


def init_solver(piece_template, piece_template_screen_width, results_path,
                cache_size):
    global solver
    solver = JumpGameSolver(results_path=results_path, cache_size=cache_size)
    solver.load_piece_template(piece_template, piece_template_screen_width)


def init_logging(level):
    logger = logging.getLogger('JumpGameSolver')
    logger.addHandler(logging.StreamHandler())
    logger.setLevel(level.upper())


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
        '--no-debug', action='store_true', help='disable flask debug mode')
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
        '--save-results',
        type=str,
        default=None,
        help='path to save images (default: disabled)')
    parser.add_argument(
        '--cache-size',
        type=int,
        default=10,
        help='piece template cache size (default: 10)')
    parser.add_argument(
        '--logging',
        type=str,
        default='DEBUG',
        help='logging level (default: DEBUG)')

    args = parser.parse_args()
    init_solver(args.piece_template, args.piece_template_screen_width,
                args.save_results, args.cache_size)
    init_logging(args.logging)
    app.run(debug=not args.no_debug, host=args.host, port=args.port)
else:
    init_solver(app.config['PIECE_TEMPLATE'],
                app.config['PIECE_TEMPLATE_SCREEN_WIDTH'],
                app.config['RESULTS_PATH'],
                app.config['PIECE_TEMPLATE_CACHE_SIZE'])
    init_logging(app.config['LOGGING_LEVEL'])
