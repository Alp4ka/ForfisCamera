import sys
import numpy as np
import cv2


def get_bounds(color):
    red = color[0]
    green = color[1]
    blue = color[2]
    color = np.uint8([[[blue, green, red]]])
    hsv_color = cv2.cvtColor(color, cv2.COLOR_BGR2HSV)
    hue = hsv_color[0][0][0]
    return (hue-15, 100, 100), (hue+15, 255, 255)
