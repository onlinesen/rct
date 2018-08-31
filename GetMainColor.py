import colorsys
from colorsys import rgb_to_hsv

colors = dict((
((255, 0, 0), "RED"),
((255, 165, 0), "ORANGE"),
((255, 205, 0), "YELLOW"),
((0, 255, 0), "GREEN"),
((0, 0, 255), "BLUE"),
((127, 0, 255), "VIOLET"),
((0, 0, 0), "BLACK"),
((255, 255, 255), "WHITE"),))

def get_dominant_color(image):
    image = image.convert('RGBA')
    image.thumbnail((200, 200))
    max_score = None
    dominant_color = None
    for count, (r, g, b, a) in image.getcolors(image.size[0] * image.size[1]):
        # ignal black
        if a == 0:
            continue
        saturation = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)[1]
        y = min(abs(r * 2104 + g * 4130 + b * 802 + 4096 + 131072) >> 13, 235)
        y = (y - 16.0) / (235 - 16)
        # ignal light
        if y > 0.9:
            continue
        # Calculate the score, preferring highly saturated colors.
        # Add 0.1 to the saturation so we don't completely ignore grayscale
        # colors by multiplying the count by zero, but still give them a low
        # weight.
        score = (saturation + 0.1) * count
        if score > max_score:
            max_score = score
            dominant_color = (r, g, b)
    return dominant_color


def to_hsv( color ):
    """ converts color tuples to floats and then to hsv """
    return rgb_to_hsv(*[x/255.0 for x in color]) #rgb_to_hsv wants floats!
def color_dist( c1, c2):
    """ returns the squared euklidian distance between two color vectors in hsv space """
    return sum( (a-b)**2 for a,b in zip(to_hsv(c1),to_hsv(c2)))
def min_color_diff( color_to_match):


    """ returns the `(distance, color_name)` with the minimal distance to `colors`"""
    return min( # overal best is the best match to any color:
        (color_dist(color_to_match, test), colors[test]) # (distance to `test` color, color name)
        for test in colors)
# color_to_match = (0,0,158)
#print min_color_diff((114, 60, 61))