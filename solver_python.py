import cv2 as cv


def find_piece(image, template, scale, blur_size, logger):
    """Find piece's center location (x, y)."""
    image = cv.blur(image, blur_size)
    # Template alread blurred in get_piece_template()
    # template = cv.blur(template, (4, 4))

    res = cv.matchTemplate(image, template, cv.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv.minMaxLoc(res)

    logger.debug('Max value in piece matching: %s', max_val)

    if max_val < 0.6:
        return None

    return max_loc[0] + int(50 * scale), max_loc[1] + int(161 * scale)


def find_shape_points(image, piece_loc, sx, sy, scale, logger):
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
        logger.info('Ignored shape: %s', (start_point, end_point))
        return None

    return start_point, end_point


def find_board_center(image, piece_loc, scale, top_keep_out_ratio, logger):
    """Find target board's center location (x, y)."""
    image = cv.Canny(image, 50, 100)  # Edge detection
    h, w = image.shape[:2]

    # Prevent the piece from being detected
    x_keepout_l = max(0, piece_loc[0] - int(50 * scale))
    x_keepout_r = min(piece_loc[0] + int(51 * scale), w)

    shape_points = None
    for y in range(int(top_keep_out_ratio * h), piece_loc[1]):
        for x in range(w):
            if image[y, x] and (x < x_keepout_l or x > x_keepout_r):
                shape_points = find_shape_points(
                    image, piece_loc, x, y, scale, logger)
                if shape_points:
                    break
        if shape_points:
            break

    if not shape_points:
        return None

    return shape_points[0][0], shape_points[1][1]
