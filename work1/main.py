# Импортируем нужные библиотеки
import numpy as np
import imutils
import cv2 as cv2
import queue
from time import sleep
from tkinter import *
from threading import Thread
from PIL import Image, ImageTk
import mean
import os
from utils import *


class ImageCarousel:
    def __init__(self):
        self.images = list()
        self.iterator = 0
        self.read_images()
        self.size = None

    def read_images(self):
        self.images = list()
        for file in os.listdir(PATH):
            if file.endswith(".jpg"):
                try:
                    self.images.append(os.path.join(PATH, file))
                    print("{0} successfully loaded!".format(os.path.join(PATH, file)))
                except Exception as ex:
                    print("Can't load {0}".format(os.path.join(PATH, file)))
                    print(str(ex))
        self.size = len(self.images)
        if self.size == 0:
            self.iterator = None
        else:
            self.iterator = 0

    def next(self):
        if self.iterator is not None:
            self.iterator = (self.iterator + 1) % self.size
        return self.iterator

    def get_current(self):
        if self.iterator is None:
            return None
        return self.images[self.iterator]


PATH = u".\\imgs"
BTN_PATH = u".\\button_colors"
PRJ_PATH = u".\\projector_colors"
COLORS = {"RED": (255, 0, 0),
          "GREEN": (0, 255, 0),
          "BLUE": (0, 0, 255),
          "YELLOW": (255, 255, 0),
          "LIGHT_BLUE": (0, 255, 255),
          "MAGENTA": (255, 0, 255),
          "LIGHT_GREEN": (95, 46, 110)}
EXIT = False


# Диалог с выбором цвета маркеров.
def markers_color_dialog():
    # Стартовое сообщение диалога.
    print("Please be sure " + PRJ_PATH + " and " + BTN_PATH + " are not empty.\n"
                                                              "Y - to continue, N - to close application:")
    ans = None
    # Получаем доступ к глобальной переменной EXIT.
    global EXIT
    while ans not in ["Y", "y", "N", "n"]:  # Начало цикла. Пока пользователь не напишет Y, y, N, n - не завершится.
        ans = input()
        if ans is not None:
            if str.lower(ans) == "n":
                EXIT = True
                print("Closing program")
                return None, None
            elif str.lower(ans) == "y":  # Если пользователь подтвердил, что папки BTN_PATH и PRJ+PATH не пусты.
                button_mean = mean.read_mean_values(BTN_PATH)
                image_mean = mean.read_mean_values(PRJ_PATH)
                if button_mean is None or image_mean is None:
                    print("No images found. Check " + BTN_PATH + " or " + PRJ_PATH + "!")
                    ans = None
                    continue
                else:
                    return button_mean, image_mean
    return None, None


class CameraCore(Thread):
    def __init__(self, queue, width=800, camera=0):  # Конструктор класса камеры
        Thread.__init__(self)
        self.queue = queue
        self.camera_number = camera
        self.window_width = width
        self.image_pointer_location = None
        self.stop = False
        self.border = None

        button_color_bounds, image_color_bounds = markers_color_dialog()
        self.colorLower_button = button_color_bounds[0]
        self.colorUpper_button = button_color_bounds[1]
        self.colorLower_image = image_color_bounds[0]
        self.colorUpper_image = image_color_bounds[1]

    def find_borders(self):  # Определяем рамки.
        (grabbed, frame) = self.camera.read()  # Читаем с камеры.
        sleep(2)  # Ждём 2 секунды, иногда первое изображение с камеры выходит плохое.
        (grabbed, frame) = self.camera.read()  # Читаем второй раз кадр.
        frame = imutils.resize(frame, width=self.window_width)  # Устанавливаем размер изображения.
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Конверт в RGB.
        img_blur = cv2.bilateralFilter(img, d=7, sigmaSpace=75, sigmaColor=75)  # Размываем для избавления от шумов.
        img_gray = cv2.cvtColor(img_blur, cv2.COLOR_RGB2GRAY)  # Переводим в градации серого.
        a = img_gray.max()  # Максимальный цвет

        _, thresh = cv2.threshold(img_gray,
                                  a / 2 - 20,
                                  a,
                                  cv2.THRESH_BINARY)  # Создаём изображение из цветов 0 и 255 по фильтру

        cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)  # Находим контуры.

        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)  # Сортируем контуры.
        img_copy = img.copy()

        final = cv2.drawContours(img_copy,
                                 cnts,
                                 contourIdx=-1,
                                 color=(255, 0, 0),
                                 thickness=2)  # Выводим контуры на изображение.
        try:  # Начинаем искать рамку.
            block1 = cv2.moments(cnts[1])  # Маркер рамки 1.
            block2 = cv2.moments(cnts[2])  # Маркер рамки 2.

            # Центр маркера 1.
            block1x = int(block1['m10'] / block1['m00'])
            block1y = int(block1['m01'] / block1['m00'])

            # Центр маркера 2.
            block2x = int(block2['m10'] / block2['m00'])
            block2y = int(block2['m01'] / block2['m00'])

            # Заводим координаты для прямоугольника.
            up_left_dot = {'x': block2x, 'y': block2y}
            down_right_dot = {'x': block1x, 'y': block1y}
            down_left_dot = {'x': up_left_dot['x'], 'y': down_right_dot['y']}
            up_right_dot = {'x': down_right_dot['x'], 'y': up_left_dot['y']}

            # Выводим вершины (для проверки).
            if DEBUG:
                print(up_left_dot)
                print(up_right_dot)
                print(down_right_dot)
                print(down_left_dot)

            # Минимальные максимальные значения вершин.
            min_x = min(up_left_dot['x'], up_right_dot['x'], down_right_dot['x'], down_left_dot['x'])
            max_x = max(up_left_dot['x'], up_right_dot['x'], down_right_dot['x'], down_left_dot['x'])
            min_y = min(up_left_dot['y'], up_right_dot['y'], down_right_dot['y'], down_left_dot['y'])
            max_y = max(up_left_dot['y'], up_right_dot['y'], down_right_dot['y'], down_left_dot['y'])

            # Держим всё в объекте класса.
            self.border = {"min_x": min_x,
                           "max_x": max_x,
                           "min_y": min_y,
                           "max_y": max_y}

            border_detected = True
        except Exception as ex:
            border_detected = False  # Рамка не найдена.
            self.border = False
            min_x = 0
            max_x = 0
            min_y = 0
            max_y = 0
            up_left_dot = {'x': None, 'y': None}
            down_right_dot = {'x': None, 'y': None}
            down_left_dot = {'x': None, 'y': None}
            up_right_dot = {'x': None, 'y': None}
            print(str(ex))
        finally:
            return min_x, max_x, min_y, max_y, up_left_dot, down_right_dot, down_left_dot, up_right_dot, border_detected

    def run(self):
        # Получаем глобальную переменную radius_image.
        global radius_image
        # Задаём значения цвета отслеживаемых точек
        # Определять через скрипт bgr_hsv_converter.py
        button_pressed = False
        change_image = False

        # Цвет точки в цнтре объекта
        image_circe_color = (0, 0, 255)

        # Подлючаем камеру, стандартно 0
        self.camera = cv2.VideoCapture(self.camera_number)
        radius_button = 0
        radius_image = 0

        # Ищем края.
        min_x, max_x, min_y, max_y, up_left_dot, down_right_dot, down_left_dot, up_right_dot, border_detected = self.find_borders()

        while True:  # Цикл работы с камерой.
            (grabbed, frame) = self.camera.read()  # Получаем текущий кадр.

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Конвертируем в RGB палитру.
            img_blur = cv2.bilateralFilter(img,
                                           d=7,
                                           sigmaSpace=75,
                                           sigmaColor=75)  # Примемяем размытие для избавления от шумов.
            img_gray = cv2.cvtColor(img_blur, cv2.COLOR_RGB2GRAY)  # Переводим в градации серого.
            a = img_gray.max()

            _, thresh = cv2.threshold(img_gray,
                                      a / 2 - 20,
                                      a,
                                      cv2.THRESH_BINARY)  # Создаём изображение из цветов 0 и 255 по фильтру.

            cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE,
                                       cv2.CHAIN_APPROX_SIMPLE)  # Находим контуры.

            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)  # Сортируем контуры.
            img_copy = img.copy()

            final = cv2.drawContours(img_copy,
                                     cnts,
                                     contourIdx=-1,
                                     color=(255, 0, 0),
                                     thickness=2)  # Выводим контуры на изображение.

            frame = imutils.resize(frame,
                                   width=self.window_width)  # Конвертируем изображение в HSV формат.
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            cv2.imshow("Frame", frame)
            cv2.waitKey(1)
            # button_color_bounds, image_color_bounds = markers_color_dialog()
            if EXIT:
                self.close()
                sleep(2)
                if self.stop:
                    break

            # self.colorLower_button = button_color_bounds[0]
            # self.colorUpper_button = button_color_bounds[1]
            # self.colorLower_image = image_color_bounds[0]
            # self.colorUpper_image = image_color_bounds[1]

            # Находим маркер кнопки по цвету
            self.colorLower_button = np.asarray(self.colorLower_button, dtype="int32")
            self.colorUpper_button = np.asarray(self.colorUpper_button, dtype="int32")
            self.colorLower_image = np.asarray(self.colorLower_image, dtype="int32")
            self.colorUpper_image = np.asarray(self.colorUpper_image, dtype="int32")

            mask_button = cv2.inRange(hsv, self.colorLower_button, self.colorUpper_button)
            mask_button = cv2.erode(mask_button, None, iterations=1)
            mask_button = cv2.dilate(mask_button, None, iterations=2)

            # Находим контуры маркера.
            cnts_button = cv2.findContours(mask_button.copy(), cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)[-2]
            center_button = None

            # Находим маркер изображения по цвету
            mask_image = cv2.inRange(hsv, self.colorLower_image, self.colorUpper_image)
            mask_image = cv2.erode(mask_image, None, iterations=2)
            mask_image = cv2.dilate(mask_image, None, iterations=2)

            # находим контуры маркера
            cnts_image = cv2.findContours(mask_image.copy(), cv2.RETR_EXTERNAL,
                                          cv2.CHAIN_APPROX_SIMPLE)[-2]
            center_image = None

            # Если маркер кнопки найден
            if len(cnts_button) > 0:
                # Находим больший контур среди всех
                c_button = max(cnts_button, key=cv2.contourArea)
                ((x, y), radius_button) = cv2.minEnclosingCircle(c_button)
                M = cv2.moments(c_button)

                # Находим центр
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

                # Проверяем радиус
                if radius_button > 10:
                    # Если радиус подходит, то рисуем круг вокруг объекта
                    # cv2.circle(frame, (int(x), int(y)), int(radius_button), (0, 255, 255), 2)
                    cv2.circle(frame, center, 5, (0, 0, 255), -1)
            change_image = False

            if radius_button < 20 and len(cnts_button) > 0:  # Если радиус кнопки маленький (кнопка перекрыта чем-то)ю
                if not button_pressed:
                    button_pressed = True
                    change_image = True
                    image_circe_color = (0, 255, 0)
            else:
                image_circe_color = (0, 0, 255)
                button_pressed = False

            if len(cnts_image) > 0:  # Если маркер изображения найденю
                c_image = max(cnts_image, key=cv2.contourArea)
                ((x, y), radius_image) = cv2.minEnclosingCircle(c_image)
                M = cv2.moments(c_image)
                center_image = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))

                if radius_image > 10:  # Проверяем радиус маркера.
                    cv2.circle(frame, (int(x), int(y)), int(radius_image),
                               (0, 255, 255), 2)  # Если радиус подходит, то рисуем круг вокруг объектаю
                    cv2.circle(frame, center_image, 5, image_circe_color, -1)
                    # Определяем и созраняем координаты центра маркера
                    self.image_pointer_location = [int(x) - min_x, int(y) - min_y]

                    if int(x) < min_x:
                        self.image_pointer_location = [0, self.image_pointer_location[1]]
                    if int(x) > max_x:
                        self.image_pointer_location = [max_x - min_x, self.image_pointer_location[1]]
                    if int(y) < min_y:
                        self.image_pointer_location = [self.image_pointer_location[0], 0]
                    if int(y) > max_y:
                        self.image_pointer_location = [self.image_pointer_location[0], max_y - min_y]
                else:
                    # Позиция маркера изображения неизветсна
                    self.image_pointer_location = None
            if border_detected:
                # Строим линии на экране.
                frame_height, frame_width = frame.shape[:2]
                cv2.line(frame, (up_left_dot['x'], up_left_dot['y']), (up_right_dot['x'], up_right_dot['y']),
                         (0, 255, 0), 2)
                cv2.line(frame, (up_right_dot['x'], up_right_dot['y']), (down_right_dot['x'], down_right_dot['y']),
                         (0, 255, 0), 2)
                cv2.line(frame, (down_right_dot['x'], down_right_dot['y']), (down_left_dot['x'], down_left_dot['y']),
                         (0, 255, 0), 2)
                cv2.line(frame, (down_left_dot['x'], down_left_dot['y']), (up_left_dot['x'], up_left_dot['y']),
                         (0, 255, 0), 2)
            # Отправляем координаты маркера и необходимость смены изображения из потока камеры
            self.queue.put_nowait([self.image_pointer_location, change_image])
            cv2.imshow("Frame", frame)  # Показываем кадр.
            cv2.waitKey(1)

            # Останока работы камеры
            if self.stop:
                break
        # Отключаем камеру и закрываем окна камеры
        self.camera.release()
        cv2.destroyAllWindows()
        return

    # Возврващаем границы
    def get_border(self):
        return self.border

    # Закрываем приложение
    def close(self):
        self.stop = True


if __name__ == "__main__":
    qe = queue.Queue()  # Задаём очередь данных для работы с потоком.
    imgs = ImageCarousel()  # Подгружаем изображения в очередь.
    camera = CameraCore(queue=qe)  # Создаём объект из класса камеры.
    camera.start()  # Запускаем работу камеры.
    border = camera.get_border()  # Получаем границы.
    while border is None or not border:  # Если границы ещё не нашлись, то ждём секунду и пробуем снова
        print('Wait for border')
        sleep(1)
        camera.find_borders()
        border = camera.get_border()
    if not border:  # Определить границы не удалось, рамку не установливаем
        print('border not detected')
        geometry = "800x600"
    else:  # А если нашлось, то задаём границы
        print("Borders found!")
        geometry = str(border['max_x'] - border['min_x']) + 'x' + str(border['max_y'] - border['min_y'])

    window = Tk()  # Создаём окно Tkinter
    # Помещаем окно в центр монитора
    x = (window.winfo_screenwidth() - window.winfo_reqwidth()) / 2
    y = (window.winfo_screenheight() - window.winfo_reqheight()) / 2
    window.wm_geometry("+%d+%d" % (x, y))
    # window.attributes("-fullscreen", True) # Если полный экран надо
    window.geometry(geometry)  # Задаём размер окна.
    window.title("Emulation")  # Заголовок окна.
    # Первая картинка.
    default_img = ImageTk.PhotoImage(Image.open("default.jpg").resize((90, 90), Image.ANTIALIAS))
    # Выбор картинки.
    img_container = Label(window, image=default_img)
    img_container.image = default_img
    # Находим координаты центра картинки.
    now_image_size = (default_img.width(), default_img.height())
    # Помещаем картинку в угол.
    img_container.place(x=0, y=0)


    # Функция изменения положения картинки
    def coordinates():
        # Берём глобальные координаты
        global now_image_size
        global img_container
        global imgs
        global radius_image
        # Забираем значения из потока через очередь
        camera_thread_data = qe.get()
        image_pointer_location = camera_thread_data[0]  # Текущие координаты картинки
        button_pressed = camera_thread_data[1]  # Нужно ли менять картинку
        new_width = max(2, int(radius_image * 2))
        if button_pressed:
            imgs.next()  # Сменить картинку в карусели.
            # Получить текущую картинку.
            temp_img = ImageTk.PhotoImage(Image.open(imgs.get_current()).resize((new_width,
                                                                                 new_width),
                                                                                 Image.ANTIALIAS))
            img_container.configure(image=temp_img)  # Конфигурируем картинку.
            img_container.image = temp_img  # Выставляем картинку.
            now_image_size = (new_width, new_width)  # Выставляем корректный размер картинки.
            window.update()  # Обновляем окно

        if image_pointer_location is not None:  # Если маркер найден, то выводим изображение в соответвующем месте/.
            im = Image.open(imgs.get_current()).resize((new_width, new_width), Image.ANTIALIAS)
            temp_img = ImageTk.PhotoImage(im)
            img_container.configure(image=temp_img)
            img_container.image = temp_img
            now_image_size = (new_width, new_width)
            img_container.place(x=image_pointer_location[0] - now_image_size[0] / 2,
                                y=image_pointer_location[1] - now_image_size[1] / 2)

            window.update()
        window.after(1, coordinates)  # Снова запускаем функцию coordinates


    coordinates()  # Выполняем coordinates
    window.mainloop()  # Запускаем работу окна с картинкой
    camera.close()  # Закрываем камеру. Происходит после закрытия окна с картинкой
