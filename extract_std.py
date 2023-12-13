import cv2
from pathlib import Path
import pymysql

# 모델 정보
BODY_PARTS = {"Neck": 1, "RShoulder": 2, "LShoulder": 5}
BASE_DIR = Path(__file__).resolve().parent
protoFile = "source\pose_deploy_linevec_faster_4_stages.prototxt"
weightsFile = "source\pose_iter_160000.caffemodel"
net = cv2.dnn.readNetFromCaffe(protoFile, weightsFile)

conn = pymysql.connect(host = 'localhost', user = 'root', password = '********', db = 'hci', charset = 'utf8')
curs = conn.cursor(pymysql.cursors.DictCursor)

# 카메라 정보
win_name ='cam'
capture = cv2.VideoCapture(0)
inputWidth = 320;
inputHeight = 240;
inputScale = 1.0 / 255;

#기준
cnt=0
ord_std=None # 정상
ext_std=None # 거북목

def onMouse(event, x, y, flags, param):
    global cnt,ord_std,ext_std
    if event == cv2.EVENT_LBUTTONDOWN:
        if cnt %2 == 0:
            ord_std = param[0]
            cnt+=1
        else:
            ext_std= param[0]
            cnt+=1
    pass

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


def cap_std(frame):
    points = []
    # NRL 추출
    extractNRL(frame, points)
    ret = frame

    if cnt % 2 == 0:
        text1 = "Maintain a proper posture for a while,"
        text2 = "then please click on the screen."
        cv2.putText(frame, text1, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, lineType=cv2.LINE_AA)
        cv2.putText(frame, text2, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, lineType=cv2.LINE_AA)
    else:
        text1 = "After making a bad posture,"
        text2 = "please click on the screen."
        cv2.putText(frame, text1, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, lineType=cv2.LINE_AA)
        cv2.putText(frame, text2, (20, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 1, lineType=cv2.LINE_AA)

    # points가 측정 가능한 삼각형을 이룸
    if isTriangle(points):

        x = abs(points[1][0] - points[2][0]) # 밑변
        h = abs(points[0][1] - (points[1][1] + points[2][1]) // 2) # 높이
        r = x // h # 비율
        cv2.putText(frame, "ratio:{0}".format(r), (250, 470), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 255), 1,
                    lineType=cv2.LINE_AA)
        cv2.line(frame, points[0], points[1], (255, 0, 0), 2)
        cv2.line(frame, points[0], points[2], (255, 0, 0), 2)

        cv2.setMouseCallback(win_name, onMouse, param=[r])

        if ord_std is not None and ext_std is not None:
            capture.release()
            cv2.destroyAllWindows()


# 카메라 재생 , 아무 키나 누르면 끝난다.
cv2.namedWindow(win_name, 1)
while cv2.waitKey(1) < 0:

    hasFrame, frame = capture.read()
    if not hasFrame:
        cv2.waitKey()
        break

    if ord_std is not None and ext_std is not None:
        sql = """ insert into reference(good, bad) values (%s, %s) """
        curs.execute(sql, (ord_std, ext_std))
        conn.commit()
        break

    cap_std(frame) #pose 점수 계산 함수 호출
    cv2.imshow(win_name,frame)

    pass

# 카메라 종료
capture.release()
cv2.destroyAllWindows()

print(ord_std,ext_std)
