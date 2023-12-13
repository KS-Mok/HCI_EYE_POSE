import cv2
import pymysql
from pathlib import Path
from datetime import datetime

# connection 정보
conn = pymysql.connect(host = 'localhost', user = 'root', password = '********', db = 'hci', charset = 'utf8')
curs = conn.cursor(pymysql.cursors.DictCursor)


# 모델 정보
BODY_PARTS = {"Neck": 1, "RShoulder": 2, "LShoulder": 5}
BASE_DIR = Path(__file__).resolve().parent
protoFile = "source\pose_deploy_linevec_faster_4_stages.prototxt"
weightsFile = "source\pose_iter_160000.caffemodel"
net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)

# 카메라 정보
capture = cv2.VideoCapture(0)
inputWidth = 320;
inputHeight = 240;
inputScale = 1.0 / 255;


ratio_cnt=0
prev_r=0
# 함수
def extractNRL(frame, points):
    # 모델로 15 점 추출
    frameWidth = frame.shape[1]
    frameHeight = frame.shape[0]
    inpBlob = cv2.dnn.blobFromImage(frame, inputScale, (inputWidth, inputHeight), (0, 0, 0), swapRB=False, crop=False)
    imgb = cv2.dnn.imagesFromBlob(inpBlob)
    net.setInput(inpBlob)
    output = net.forward()

    # NRL 정보 추출
    mat = [1, 2, 5]
    for j in range(3):
        i = mat[j]
        probMap = output[0, i, :, :]
        minVal, prob, minLoc, point = cv2.minMaxLoc(probMap)
        x = (frameWidth * point[0]) / output.shape[3]
        y = (frameHeight * point[1]) / output.shape[2]

        # NRL 검출한 결과가 0.1보다 크면 points 추가, 아니면 None
        if prob > 0.1:
            points.append((int(x), int(y)))
        else:
            points.append(None)
    pass


def isTriangle(points):
    if points[0] and points[1] and points[2]: # 3점 다 찍힘
        if (points[1][0] < points[0][0]) and (points[0][0]<points[2][0]): # x좌표가 RNL 순
            if points[0][1] < min(points[1][1],points[2][1]): # y 좌표가 N이 작음
                return True
    return False


def score_turtle(frame,curs, ord_ratio, ext_ratio):
    # print(f"Latest 'good' value: {ord_ratio}")
    # print(f"Latest 'bad' value: {ext_ratio}")

    points = []
    # NRL 추출
    extractNRL(frame, points)
    ret = frame
    # points가 측정 가능한 삼각형을 이룸
    if isTriangle(points):
        x = abs(points[1][0] - points[2][0]) # 밑변
        h = abs(points[0][1] - (points[1][1] + points[2][1]) // 2) # 높이
        r = x /h # 비율

        step = (ext_ratio - ord_ratio)/4

        if r <= ord_ratio:
            cv2.line(frame, points[0], points[1], (255, 0, 0), 2)
            cv2.line(frame, points[0], points[2], (255, 0, 0), 2)
            score = 100
        elif r <= ord_ratio+step:
            cv2.line(frame, points[0], points[1], (0, 255, 0), 2)
            cv2.line(frame, points[0], points[2], (0, 255, 0), 2)
            score = 80
        elif r <= ord_ratio + 2*step:
            cv2.line(frame, points[0], points[1], (0, 255, 255), 2)
            cv2.line(frame, points[0], points[2], (0, 2555, 255), 2)
            score = 60
        elif r <= ord_ratio + 3*step:
            cv2.line(frame, points[0], points[1], (0, 165, 255), 2)
            cv2.line(frame, points[0], points[2], (0, 165, 255), 2)
            score = 40
        else:
            cv2.line(frame, points[0], points[1], (0, 0, 255), 2)
            cv2.line(frame, points[0], points[2], (0, 0, 255), 2)
            score = 20

        global prev_r,ratio_cnt
        if ratio_cnt <=4 and prev_r != r:
            # DB
            sql = """ insert into score(score, createdAt) values (%s, %s) """
            curs.execute(sql, (score, datetime.now()))
            conn.commit()
            print("db 저장됨")
            ratio_cnt+=1
            pass
        prev_r = r
        pass

    return ret


# 카메라 재생 , 아무 키나 누르면 끝난다.
ord_ratio = 3
ext_ratio = 7

curs.execute("SELECT good, bad FROM reference")
all_values = curs.fetchall()
if all_values:

    ord_ratio = all_values[-1]['good']
    ext_ratio = all_values[-1]['bad']
else:
    pass

while cv2.waitKey(1) < 0:

    hasFrame, frame = capture.read()
    if not hasFrame:
        cv2.waitKey()
        break

    res = score_turtle(frame, curs, ord_ratio, ext_ratio) #pose 점수 계산 함수 호출

    if ratio_cnt == 5:
        break
    cv2.imshow("posture", res)
    pass

# 카메라 종료
capture.release()
cv2.destroyAllWindows()

