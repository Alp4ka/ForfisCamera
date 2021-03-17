from PIL import Image, ImageFilter
import os
import bgr_hsv_converter

def get_mean_color(image):
    w, h = image.size
    '''rr, gg, bb = 0, 0, 0

    for x in range(w):
        for y in range(h):
            r, g, b = image.getpixel((x, y))
            rr += r
            gg += g
            bb += h

    cnt = w * h'''
    image = image.filter(ImageFilter.GaussianBlur(max(w, h)))
    r, g, b= image.getpixel((w//2, h//2))
    print("real mean: ", *[r, g, b])
    return bgr_hsv_converter.get_bounds([r, g, b])


def read_mean_values(directory):
    try:
        files = os.listdir(directory)
        if len(files) > 0:
            file = os.listdir(directory)[0]
            image = Image.open(os.path.join(directory, file))
            temp = get_mean_color(image)
            print(os.path.join(directory, file) + " lower mean is " + str(temp[0][0]) + ", " + str(temp[0][1]) + ", " +
                  str(temp[0][2]))
            print(os.path.join(directory, file) + " upper mean is " + str(temp[1][0]) + ", " + str(temp[1][1]) + ", " +
                  str(temp[1][2]))
            return temp
        else:
            return None
    except Exception as ex:
        print("Can't count mean of {0}".format(os.path.join(directory, file)))
        print(str(ex))
        return None
