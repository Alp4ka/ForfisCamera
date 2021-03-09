# Импортируем нужные библиотеки
from collections import deque
import numpy as np
import argparse
import imutils
import cv2 as cv2
import queue
from time import sleep
from tkinter import *
from threading import Thread
from PIL import Image, ImageTk


class CameraCore(Thread):
    def __init__(self, queue, width=800, camera=0):
        # Конструктор класса камеры
        Thread.__init__(self)
        self.queue = queue
        self.camera_number = camera
        self.window_width = width
        self.image_pointer_location = None
        self.stop = False
        self.border = None

    def run(self):
        # Задаём значения цвета отслеживаемых точек
        # Определять через скрипт bgr_hsv_converter.py
        colorLower_button = (91, 100, 100)  # СИНИЙ
        colorUpper_button = (111, 255, 255)
        colorLower_image = (15, 100, 100) # ЖЁЛТЫЙ
        colorUpper_image = (35, 255, 255)
        BUTTON_PRESSED = False
        CHANGE_IMAGE = False
        # Цвет точки в цнтре объекта
        image_circe_color = (0, 0, 255)  # КРАСНЫЙ
        # Подлючаем камеру, стандартно 0
        camera = cv2.VideoCapture(self.camera_number)
        radius_button = 0
        radius_image = 0
        ################################
        #### БЛОК ОПРЕДЕЛЕНИЯ РАМОК ####
        ####         НАЧАЛО         ####
        ################################
        bordLower_image = (0, 40, 40)  # ЖЁЛТЫЙ
        bordUpper_image = (123, 123, 123)
        # Читаем с камеры
        (grabbed, frame) = camera.read()
        sleep(2)  # Ждём 2 секунды, иногда первое изображение с камеры выходит плохое
        # Читаем второй раз кадр
        (grabbed, frame) = camera.read()
        # Устанавливаем размер изображения
        frame = imutils.resize(frame, width=self.window_width)
        # Конверт в RGB
        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Примемяем размытие для избавления от шумов
        img_blur = cv2.bilateralFilter(img, d=7,
                                       sigmaSpace=75, sigmaColor=75)
        # Переводим в цвета серого
        img_gray = cv2.cvtColor(img_blur, cv2.COLOR_RGB2GRAY)
        a = img_gray.max()  # Максимальный цвет
        # Создаём изображение из цветов 0 и 255 по фильтру
        _, thresh = cv2.threshold(img_gray, a / 2 - 20, a, cv2.THRESH_BINARY)
        # Находим контуры
        cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE,
                                   cv2.CHAIN_APPROX_SIMPLE)
        # Сортируем контуры
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        img_copy = img.copy()
        # Выводим контуры на изображение
        final = cv2.drawContours(img_copy, cnts, contourIdx=-1,
                                 color=(255, 0, 0), thickness=2)
        try:  # Начинаем искать рамку
            BlockOne = cv2.moments(cnts[1])  # Маркер рамки 1
            BlockTwo = cv2.moments(cnts[2])  # Маркер рамки 2
            # Центр маркера 1
            BlockOneX = int(BlockOne['m10'] / BlockOne['m00'])
            BlockOneY = int(BlockOne['m01'] / BlockOne['m00'])
            # Центр маркера 2
            BlockTwoX = int(BlockTwo['m10'] / BlockTwo['m00'])
            BlockTwoY = int(BlockTwo['m01'] / BlockTwo['m00'])
            # Заводим координаты для прямоугольника
            up_left_dot = {'x': BlockTwoX, 'y': BlockTwoY}
            down_right_dot = {'x': BlockOneX, 'y': BlockOneY}
            down_left_dot = {'x': None, 'y': None}
            up_right_dot = {'x': None, 'y': None}
            # Задаём вершины прямоугольника
            down_left_dot['x'] = up_left_dot['x']
            down_left_dot['y'] = down_right_dot['y']
            up_right_dot['x'] = down_right_dot['x']
            up_right_dot['y'] = up_left_dot['y']
            # Выводим вершины (для проверки)
            print(up_left_dot)
            print(up_right_dot)
            print(down_right_dot)
            print(down_left_dot)
            # Минимальные максимальные значения вершин
            min_x = min(up_left_dot['x'], up_right_dot['x'], down_right_dot['x'], down_left_dot['x'])
            max_x = max(up_left_dot['x'], up_right_dot['x'], down_right_dot['x'], down_left_dot['x'])
            min_y = min(up_left_dot['y'], up_right_dot['y'], down_right_dot['y'], down_left_dot['y'])
            max_y = max(up_left_dot['y'], up_right_dot['y'], down_right_dot['y'], down_left_dot['y'])
            # Держим всё в объекте класса
            self.border = {"min_x": min_x,
                           "max_x": max_x,
                           "min_y": min_y,
                           "max_y": max_y}

            border_detected = True
        except:
            # Рамка не найдена
            border_detected = False
            self.border = False
        ################################
        #### БЛОК ОПРЕДЕЛЕНИЯ РАМОК ####
        ####         КОНЕЦ          ####
        ################################
        # Цикл работы с камерой
        while True:
            # Получаем текущий кадр
            (grabbed, frame) = camera.read()
            # Конвертируем в RGB палитру
            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Примемяем размытие для избавления от шумов
            img_blur = cv2.bilateralFilter(img, d=7,
                                           sigmaSpace=75, sigmaColor=75)
            # Переводим в цвета серого
            img_gray = cv2.cvtColor(img_blur, cv2.COLOR_RGB2GRAY)
            a = img_gray.max()
            # Создаём изображение из цветов 0 и 255 по фильтру
            _, thresh = cv2.threshold(img_gray, a / 2 - 20, a, cv2.THRESH_BINARY)
            # Находим контуры
            cnts, _ = cv2.findContours(thresh, cv2.RETR_TREE,
                                       cv2.CHAIN_APPROX_SIMPLE)
            # Сортируем контуры
            cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
            img_copy = img.copy()
            # Выводим контуры на изображение
            final = cv2.drawContours(img_copy, cnts, contourIdx=-1,
                                     color=(255, 0, 0), thickness=2)
            # Конвертируем изображение в HSV формат
            frame = imutils.resize(frame, width=self.window_width)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            # Находим маркер кнопки по цвету
            mask_button = cv2.inRange(hsv, colorLower_button, colorUpper_button)
            mask_button = cv2.erode(mask_button, None, iterations=2)
            mask_button = cv2.dilate(mask_button, None, iterations=2)
            # находим контуры маркера
            cnts_button = cv2.findContours(mask_button.copy(), cv2.RETR_EXTERNAL,
                                           cv2.CHAIN_APPROX_SIMPLE)[-2]
            center_button = None
            # Находим маркер изображения по цвету
            mask_image = cv2.inRange(hsv, colorLower_image, colorUpper_image)
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
                    cv2.circle(frame, (int(x), int(y)), int(radius_button),
                               (0, 255, 255), 2)
                    cv2.circle(frame, center, 5, (0, 0, 255), -1)
            CHANGE_IMAGE = False
            # Если радиус кнопки маленький (кнопка перекрыта чем-то)
            if radius_button < 20:
                if BUTTON_PRESSED == False:
                    BUTTON_PRESSED = True
                    CHANGE_IMAGE = True
                    image_circe_color = (0, 255, 0)
            else:
                image_circe_color = (0, 0, 255)
                BUTTON_PRESSED = False
            # Если маркер изображения найден
            if len(cnts_image) > 0:
                c_image = max(cnts_image, key=cv2.contourArea)
                ((x, y), radius_image) = cv2.minEnclosingCircle(c_image)
                M = cv2.moments(c_image)
                center_image = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                # Проверяем радиус маркера
                if radius_image > 10:
                    # Если радиус подходит, то рисуем круг вокруг объекта
                    cv2.circle(frame, (int(x), int(y)), int(radius_image),
                               (0, 255, 255), 2)
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
                ## Строим линии на экране
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
            self.queue.put_nowait([self.image_pointer_location, CHANGE_IMAGE])
            # Показываем кадр
            cv2.imshow("Frame", frame)
            cv2.waitKey(1)

            # Останока работы камеры
            if self.stop == True:
                break
        # Отключаем камеру и закрываем окна камеры
        camera.release()
        cv2.destroyAllWindows()

    # Возврващаем границы
    def get_border(self):
        return self.border

    # Закрываем приложение
    def close(self):
        self.stop = True


if __name__ == "__main__":
    # Задаём очередь данных для работы с потоком
    qe = queue.Queue()
    # Создаём объект из класса камеры
    camera = CameraCore(queue=qe)
    # Запускаем работу камеры
    camera.start()
    # Получаем границы
    border = camera.get_border()
    while border == None:  # Если границы ещё не нашлись, то ждём секунду и пробуем снова
        print('Wait for border')
        sleep(1)
        border = camera.get_border()
    if border == False:  # Определить границы не удалось, рамку не установливаем
        print('border not detected')
        geometry = "800x600"
    else:  # А если нашлось, то задаём границы
        geometry = str(border['max_x'] - border['min_x']) + 'x' + str(border['max_y'] - border['min_y'])
    window = Tk()  # Создаём окно Tkinter
    # Помещаем окно в центр монитора
    x = (window.winfo_screenwidth() - window.winfo_reqwidth()) / 2
    y = (window.winfo_screenheight() - window.winfo_reqheight()) / 2
    window.wm_geometry("+%d+%d" % (x, y))
    # window.attributes("-fullscreen", True) # Если полный экран надо
    window.geometry(geometry)  # Задаём размер окна
    window.title("Proektor")  # Заголовок окна
    ## Первая картинка
    kianu_riwz = ImageTk.PhotoImage(Image.open("kianu_riwz.jpg").resize((90, 90), Image.ANTIALIAS))
    ## Вторая картинка
    jouen_jonson = ImageTk.PhotoImage(Image.open("jouen_jonson.jpg").resize((90, 90), Image.ANTIALIAS))
    ## Выбор картинки
    img_container = Label(window, image=kianu_riwz)
    img_container.image = kianu_riwz
    now_is_image = 'kianu_riwz'
    # Находм координаты центра картинки
    now_image_size = (kianu_riwz.width() / 2, kianu_riwz.height() / 2)
    # Помещаем картинку в угол
    img_container.place(x=0, y=0)


    # Функция изменения положения картинки
    def coordinates():
        # Берём глобальные координаты
        global now_image_size
        global now_is_image
        global img_container
        # Забираем значения из потока через очередь
        camera_thread_data = qe.get()
        image_pointer_location = camera_thread_data[0]  # Текущие координаты картинки
        button_pressed = camera_thread_data[1]  # Нужно ли менять картинку
        if button_pressed:  # Производим замену картинки
            print(now_is_image)
            if now_is_image == 'kianu_riwz':
                img_container.configure(image=jouen_jonson)
                img_container.image = jouen_jonson
                now_is_image = 'jouen_jonson'
                now_image_size = (jouen_jonson.width() / 2, jouen_jonson.height() / 2)
            else:
                img_container.configure(image=kianu_riwz)
                img_container.image = kianu_riwz
                now_is_image = 'kianu_riwz'
                now_image_size = (kianu_riwz.width() / 2, kianu_riwz.height() / 2)
            window.update()  # Обновляем окно
        if image_pointer_location != None:  # Если маркер изображения найден, то в Tkinter выводим изображение в соответвующем месте
            img_container.place(x=image_pointer_location[0] - now_image_size[0],
                                y=image_pointer_location[1] - now_image_size[1])
            window.update()
        window.after(1, coordinates)  # Снова запускаем функцию coordinates


    coordinates()  # Выполняем coordinates
    window.mainloop()  # Запускаем работу окна с картинкой
    camera.close()  # Закрываем камеру. Происходит после закрытия окна с картинкой
