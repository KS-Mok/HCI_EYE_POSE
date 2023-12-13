from scipy.spatial import distance
from imutils import face_utils
import imutils
import dlib
import cv2
import time
import threading
from cv2 import CAP_PROP_FRAME_HEIGHT, CAP_PROP_FRAME_WIDTH
import numpy as np
from PIL import Image, ImageFont
from PIL import ImageDraw
import torch
import tkinter
import tkinter.messagebox
from PIL import ImageTk
import pygame
pygame.init()

# 졸음감지 - 눈 비율 계산 
def eye_aspect_ratio(eye):
	A = distance.euclidean(eye[1], eye[5])
	B = distance.euclidean(eye[2], eye[4])
	C = distance.euclidean(eye[0], eye[3])
	ear = (A + B) / (2.0 * C)
	return ear
	
# 졸음감지 - 변수, 기타설정, dat 파일 불러오기 
thresh = 0.25
frame_check = 15
detect = dlib.get_frontal_face_detector()
predict = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")# Dat file is the crux of the code
(lStart, lEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["left_eye"]
(rStart, rEnd) = face_utils.FACIAL_LANDMARKS_68_IDXS["right_eye"]
cap=cv2.VideoCapture(0)
global flag
flag=0

# 이제 정신이 드니..? 이미지 팝업
def show_popup(image_path):
    popup = tkinter.Tk()
    popup.title("Wake Up!")
    # 이미지 불러오기
    image = Image.open(image_path)
    dog_image = ImageTk.PhotoImage(image)
    # 라벨에 이미지 추가
    label = tkinter.Label(popup, image=dog_image)
    label.pack()
    # 창 크기와 위치 설정 - center
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    dog_width, dog_height = 400, 300
    x = (screen_width - dog_width) // 2
    y = (screen_height - dog_height) // 2
    popup.geometry(f"{dog_width}x{dog_height}+{x}+{y}")
    # 창을 3초 동안 유지
    popup.after(5000, popup.destroy)
    popup.mainloop()
def load_and_show_popup(image_path):
    # 이미지 로딩 및 팝업 창 표시
    show_popup(image_path)

# 미로 만들기
def make_maze():
    global maze, canvas, root, mx, my, state, key, resize_rate, iris_x_threshold, iris_y_threshold, cap, iris_status, left_x_per
    mx = 1  # 캐릭터의 가로 뱡향 위치를 관리하는 변수
    my = 5  # 캐릭터의 세로 뱡향 위치를 관리하는 변수
    state = 0  # 게임 상황, 0: 게임 진행, 1: 게임 클리어, 2: 게임 클리어 불가능
    key = 0  # 키 이름을 입력할 변수 선언

    # 미로 초기화, 세팅
    maze = [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 1, 1, 1, 1, 1, 1, 0, 1],
        [1, 0, 1, 0, 0, 0, 1, 1, 0, 1],
        [1, 0, 1, 0, 1, 1, 1, 1, 0, 1],
        [1, 0, 1, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ]
    resize_rate = 1
    iris_status, left_x_per = 'Center', 'None'

    # 미로 canvas 불러오기 
    root = tkinter.Tk()
    root.title("미로를 칠하는 중")
    root.bind("<KeyPress>", lambda e: key_down(e))
    root.bind("<KeyRelease>", lambda e: key_up(e))
    canvas = tkinter.Canvas(width=800, height=560, bg="white")
    canvas.pack()

# 미로 - def로 함수 정의 
def key_down(e):
    global key  # key을 전역 변수로 취급
    key = e.keysym  # 눌려진 키 이름을 key에 대입

def key_up(e):
    global key  # key을 전역 변수로 취급
    key = ""  # key에 빈 문자열 대입

def move():
    global mx, my, iris_status
    if iris_status == 'Up' and maze[my - 1][mx] == 0:
        my -= 1
    if iris_status == 'Down' and maze[my + 1][mx] == 0:
        my += 1
    if iris_status == 'Left' and maze[my][mx - 1] == 0:
        mx -= 1
    if iris_status == 'Right' and maze[my][mx + 1] == 0:
        mx += 1

    if maze[my][mx] == 0:
        maze[my][mx] = 2
        canvas.create_oval(mx * 80, my * 80, mx * 80 + 79, my * 80 + 79,
                                fill="pink", width=0, tag="PAINT")
    canvas.delete("MYCHR")

def count_tile():
    cnt = 0
    for i in range(7):
        for j in range(10):
            if maze[i][j] == 0:
                cnt += 1
    return cnt

def check():
    cnt = count_tile()
    if 0 not in [maze[my - 1][mx], maze[my + 1][mx], maze[my][mx - 1], maze[my][mx + 1]]:
        print("2")
        return 2
    elif cnt == 0:
        print("1")
        return 1
    else:
        print(0)
        return 0

def reset():
    global mx, my, state
    state = 0
    canvas.delete("PAINT")
    mx = 1
    my = 1
    for y in range(7):
        for x in range(10):
            if maze[y][x] == 2:
                maze[y][x] = 0

def draw_maze():
    for y in range(7):
        for x in range(10):
            if maze[y][x] == 1:
                canvas.create_rectangle(x * 80, y * 80, x * 80 + 79, y * 80 + 79, fill="skyblue", width=0)

def draw_character():
    global mx, my, iris_status
    x = mx * 80 + 40
    y = my * 80 + 40

    if iris_status == 'Up':
        canvas.create_text(x, y - 30, text="^", font=("Helvetica", 16), fill="red")
    elif iris_status == 'Down':
        canvas.create_text(x, y + 30, text="v", font=("Helvetica", 16), fill="red")
    elif iris_status == 'Left':
        canvas.create_text(x - 30, y, text="<", font=("Helvetica", 16), fill="red")
    elif iris_status == 'Right':
        canvas.create_text(x + 30, y, text=">", font=("Helvetica", 16), fill="red")

def yolo_process(img):
    yolo_results = model(img)
    df = yolo_results.pandas().xyxy[0]
    obj_list = []
    for i in range(len(df)) :
        obj_confi = round(df['confidence'][i], 2)
        obj_name = df['name'][i]
        x_min = int(df['xmin'][i])
        y_min = int(df['ymin'][i])
        x_max = int(df['xmax'][i])
        y_max = int(df['ymax'][i])
        obj_dict = {
                    'class' : obj_name, 
                    'confidence' : obj_confi,
                    'xmin' : x_min,
                    'ymin' : y_min,
                    'xmax' : x_max, 
                    'ymax' : y_max
        }
        obj_list.append(obj_dict)
    return obj_list

# 미로 - 모델 불러오기
model = torch.hub.load('ultralytics/yolov5', 'custom', path = 'best.pt')
model.conf = 0.3
model.iou = 0
resize_rate = 1
iris_x_threshold, iris_y_threshold = 0.15, 0.26 # 눈동자가 중앙에서 얼마나 벗어나야 상태 바뀜으로 인정할 것인지
cap = cv2.VideoCapture(0)
iris_status = 'Center'
left_x_per = 'None'

# 미로 - 함수 지정 - 실제 cam on, iris detect, 미로찾기 실행
def main_maze():
    make_maze()

    global mx, my, state, key, iris_status, left_x_per
    while True:
        if key == "Escape":
            key = 0
            ret = tkinter.messagebox.askyesno("종료", "게임을 종료하시겠습니까?")
            if ret:
                root.destroy()
                return

        if key == "Shift_L":
            reset()

        state = check()

        if state == 0:
            move()

        if state == 1:
            tkinter.messagebox.showinfo("축하합니다!", "모든 바닥을 칠했습니다!")
            # #reset()
            cv2.destroyAllWindows()
            root.destroy()
            return

        if state == 2:
            tkinter.messagebox.showinfo("축하합니다!", "모든 바닥을 칠했습니다!")
            reset()
            root.destroy()     
            return

        draw_maze()
        draw_character()

        ret, img = cap.read()
        if not ret:
            break

        imgS = cv2.resize(img, (0, 0), None, resize_rate, resize_rate)
        results = yolo_process(imgS)

        eye_list = []
        iris_list = []

        for result in results:
            if result['class'] == 'iris':
                x_length = int(result['xmax']) - int(result['xmin'])
                y_length = int(result['ymax']) - int(result['ymin'])
                circle_r = int((x_length + y_length) / 4)
                x_center = int((int(result['xmin']) + int(result['xmax'])) / 2)
                y_center = int((int(result['ymin']) + int(result['ymax'])) / 2)
                cv2.circle(img, (x_center, y_center), circle_r, (255, 255, 255), 1)
            if result['class'] == 'eye':
                eye_list.append(result)
            elif result['class'] == 'iris':
                iris_list.append(result)

        if len(eye_list) == 2 and len(iris_list) == 2:
            left_part = []
            right_part = []
            if eye_list[0]['xmin'] > eye_list[1]['xmin']:
                right_part.append(eye_list[0])
                left_part.append(eye_list[1])
            else:
                right_part.append(eye_list[1])
                left_part.append(eye_list[0])

            if iris_list[0]['xmin'] > iris_list[1]['xmin']:
                right_part.append(iris_list[0])
                left_part.append(iris_list[1])
            else:
                right_part.append(iris_list[1])
                left_part.append(iris_list[0])

            # 왼쪽 눈동자의 위치 비율
            left_x_iris_center = (left_part[1]['xmin'] + left_part[1]['xmax']) / 2
            left_x_per = (left_x_iris_center - left_part[0]['xmin']) / (left_part[0]['xmax'] - left_part[0]['xmin'])
            left_y_iris_center = (left_part[1]['ymin'] + left_part[1]['ymax']) / 2
            left_y_per = (left_y_iris_center - left_part[0]['ymin']) / (left_part[0]['ymax'] - left_part[0]['ymin'])

            # 오른쪽 눈동자의 위치 비율
            right_x_iris_center = (right_part[1]['xmin'] + right_part[1]['xmax']) / 2
            right_x_per = (right_x_iris_center - right_part[0]['xmin']) / (right_part[0]['xmax'] - right_part[0]['xmin'])
            right_y_iris_center = (right_part[1]['ymin'] + right_part[1]['ymax']) / 2
            right_y_per = (right_y_iris_center - right_part[0]['ymin']) / (right_part[0]['ymax'] - right_part[0]['ymin'])

            # 왼쪽 눈동자와 오른쪽 눈동자 비율의 평균
            avr_x_iris_per = (left_x_per + right_x_per) / 2
            avr_y_iris_per = (left_y_per + right_y_per) / 2

            # Threshold 기준으로 눈동자의 위치를 계산
            if avr_x_iris_per < (0.5 - iris_x_threshold):
                iris_status = 'Left'
                print("Left : ((", avr_x_iris_per < (0.5 - iris_x_threshold), "))", "avr_x_iris_per : ", avr_x_iris_per, "iris_x_threshold : ", iris_x_threshold, "avr_y_iris_per : ", avr_y_iris_per, "iris_y_threshold : ", iris_y_threshold)
                move()
            elif avr_x_iris_per > (0.5 + iris_x_threshold):
                iris_status = 'Right'
                print("Right : ((", avr_x_iris_per > (0.5 + iris_x_threshold), "))", "avr_x_iris_per : ", avr_x_iris_per, "iris_x_threshold : ", iris_x_threshold, "avr_y_iris_per : ", avr_y_iris_per, "iris_y_threshold : ", iris_y_threshold)
                move()
            #elif avr_y_iris_per > (0.5 - iris_y_threshold):
            elif avr_y_iris_per > (0.6):
                iris_status = 'Up'
                print("Up : ((", avr_y_iris_per > (0.6), "))", "avr_x_iris_per : ", avr_x_iris_per, "iris_x_threshold : ", iris_x_threshold, "avr_y_iris_per : ", avr_y_iris_per, "iris_y_threshold : ", iris_y_threshold)
                move()
            else:
                iris_status = 'Center'
                print("Center 에서 Up : ((", avr_y_iris_per > (0.6 - iris_y_threshold), "))")
                print("Center : ", "avr_x_iris_per : ", avr_x_iris_per, "iris_x_threshold : ", iris_x_threshold, "avr_y_iris_per : ", avr_y_iris_per, "iris_y_threshold : ", iris_y_threshold)

        elif len(iris_list) == 0:      # 눈을 아예 감으면 down으로 인식하게 함 
        #elif len(eye_list) == 2 and len(iris_list) == 0:
            iris_status = 'Down'
            move()

        cv2.putText(img, 'The pupils are looking to the {}'.format(iris_status), (10, 40), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 0), 2)
        cv2.imshow('Which direction are you looking at?', img)
        cv2.waitKey(1)

        root.update_idletasks()
        root.update()

# 졸음감지 코드 함수로 묶음 
def main_sleep_detect():
    global flag
    while True:
        ret, frame=cap.read()
        frame = imutils.resize(frame, width=450)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        subjects = detect(gray, 0)
        for subject in subjects:
            shape = predict(gray, subject)
            shape = face_utils.shape_to_np(shape)     #converting to NumPy Array
            leftEye = shape[lStart:lEnd]
            rightEye = shape[rStart:rEnd]
            leftEAR = eye_aspect_ratio(leftEye)
            rightEAR = eye_aspect_ratio(rightEye)
            ear = (leftEAR + rightEAR) / 2.0
            leftEyeHull = cv2.convexHull(leftEye)
            rightEyeHull = cv2.convexHull(rightEye)
            cv2.drawContours(frame, [leftEyeHull], -1, (0, 255, 0), 1)
            cv2.drawContours(frame, [rightEyeHull], -1, (0, 255, 0), 1)
            if ear < thresh:
                time.sleep(0.2)
                flag += 1
                print (flag)
                if flag == frame_check:
                    sound1 = pygame.mixer.Sound("80s_Phone.ogg")
                    sound1.play()
                if flag >= frame_check:
                    cv2.putText(frame, "****************ALERT!****************", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    cv2.putText(frame, "****************ALERT!****************", (10,325),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

                if flag == 30:
                    sound2 = pygame.mixer.Sound("sleepalarm.mp3")
                    sound2.play()
                    flag=0
                    cv2.destroyAllWindows()
                    # 미로 실행
                    main_maze()
                    cv2.destroyAllWindows()
                    # 정신이 드니..? popup
                    image_path = "wakeupdog.jpeg"
                    threading.Thread(target=load_and_show_popup, args=(image_path,)).start()
                    
            else:
                flag = 0
        cv2.imshow("Frame", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
    cv2.destroyAllWindows()
    cap.release() 
	
# 졸음감지 코드 실행
main_sleep_detect()


