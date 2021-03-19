from PIL import Image, ImageFilter
import os
import bgr_hsv_converter
from utils import *


# Считает средний цвет изображения(весьма странным образом).
def get_mean_color(image):
    w, h = image.size  # Получает размеры изображения.
    image = image.filter(ImageFilter.GaussianBlur(max(w, h)))  # Применяет сильное размытие на изображение.
    r, g, b = image.getpixel((w//2, h//2))  # Получает значение в самом среднем пикселе.
    if DEBUG:
        print("real mean: ", *[r, g, b])
    return bgr_hsv_converter.get_bounds([r, g, b])


# Прочиать изображение в директории и вычислить средний цвет.
def read_mean_values(directory):
    try:
        files = os.listdir(directory)  # Получить все файлы в директории.
        if len(files) > 0:  # Если файлы есть.
            file = os.listdir(directory)[0]  # Выбираем первый файл.
            image = Image.open(os.path.join(directory, file))  # Загружаем в image изображение.
            temp = get_mean_color(image)
            if DEBUG:
                print("{0} lower mean is {1},{2},{3}".format(os.path.join(directory, file),
                                                             str(temp[0][0]),
                                                             str(temp[0][1]),
                                                             str(temp[0][2])))
                print("{0} lower mean is {1},{2},{3}".format(os.path.join(directory, file),
                                                             str(temp[1][0]),
                                                             str(temp[1][1]),
                                                             str(temp[1][2])))
            return temp
        else:
            return None
    except Exception as ex:
        print("Can't count mean of {0}".format(os.path.join(directory, file)))
        print(str(ex))
        return None
