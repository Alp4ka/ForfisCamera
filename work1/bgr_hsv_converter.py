import sys
import numpy as np
import cv2


# Получает границы цвета по ргб палитре, конвертя их в HSV.
def get_bounds(color):
    red = color[0]
    green = color[1]
    blue = color[2]
    color = np.uint8([[[blue, green, red]]])  # Переводим в формат нампаевского массива.
    hsv_color = cv2.cvtColor(color, cv2.COLOR_BGR2HSV)  # Конвертим rgb->hsv.
    hue = hsv_color[0][0]  # Получаем [h, s, v].
    upper = (hue[0] + 10, hue[1] + 10, hue[2] + 40)  # Верхняя граница.
    lower = (hue[0] - 10, hue[1] - 10, hue[2] - 40)  # Нижняя граница.
    return lower, upper
