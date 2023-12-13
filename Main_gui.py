import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt
import subprocess


# 아이, 모션 통합된 거 GUI

class CustomWidget(QWidget):
    def __init__(self):
        super().__init__()

        # 박스의 색상 및 파일 매핑
        #self.box_colors = [(201, 241, 248), (201, 248, 215), (248, 215, 201)]
        self.box_colors = [(201, 241, 248), (201, 248, 215), (239, 223, 250), (248, 215, 201)]
        # self.file_paths = ['hci.py','extract_std.py','final_main.py','calendar.py']
        self.file_paths = ['hci.py', 'extract_std.py', 'calendar_1.py']

        # 박스를 클릭할 때 실행할 함수 연결
        self.box_click_handlers = [self.open_all, self.open_ref, self.open_result]

        # 결과 창을 저장할 변수 추가
        self.result_widget = None

        self.init_ui()

    def init_ui(self):
        self.setGeometry(200, 200, 500, 400)
        self.setWindowTitle('Main ')

        # 박스를 표시할 QLabel들을 만듭니다.
        self.labels = [QLabel(self) for _ in range(3)]
        # self.labels = [QLabel(self) for _ in range(4)]

        # 박스의 배경색 및 텍스트 설정
        for i, label in enumerate(self.labels):
            color = QColor(*self.box_colors[i])
            label.setAutoFillBackground(True)
            label.setStyleSheet(f"QLabel {{ background-color: {color.name()}; }}")
            label.setAlignment(Qt.AlignCenter)
            labels_text = ['모니터링 시작', '자세 기준값', '자세 결과']
            #labels_text = ['눈', '자세 기준값 잡기','자세 모니터링 시작','자세 결과']
            label.setText(labels_text[i])
            label.mousePressEvent = lambda event, idx=i: self.on_box_click(idx)

        # QVBoxLayout을 사용하여 박스들을 수직으로 배치합니다.
        layout = QVBoxLayout(self)
        for label in self.labels:
            layout.addWidget(label)

        self.show()

    def on_box_click(self, idx):
        # 박스를 클릭했을 때 실행할 함수 호출
        self.box_click_handlers[idx]()

    def open_all(self):
        subprocess.Popen(['python', self.file_paths[0]])

    def open_ref(self):
        subprocess.Popen(['python', self.file_paths[1]])

    # def open_posture(self):
    #     subprocess.Popen(['python', self.file_paths[2]])

    def open_result(self):
        #print("Opening file:", self.file_paths[1])
        subprocess.Popen(['python', self.file_paths[2]])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    widget = CustomWidget()
    sys.exit(app.exec_())
