import sys
from PyQt5.QtCore import Qt, QRectF, QDate
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtWidgets import QCalendarWidget, QApplication
import pymysql

class CalendarWidget(QCalendarWidget):

    def __init__(self, parent=None):
        super(CalendarWidget, self).__init__(parent)
        self.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)  # Hide week numbers

        # Establish a database connection
        self.db_connection = pymysql.connect(
            host='localhost',
            user='root',
            password='********',
            database='hci',
            charset='utf8'
        )
        self.cursor = self.db_connection.cursor()

    def paintCell(self, painter, rect, date):
        painter.setRenderHint(QPainter.Antialiasing, True)

        painter.save()

        # Set different colors for weekends and weekdays
        if date.dayOfWeek() == Qt.Saturday or date.dayOfWeek() == Qt.Sunday:
            painter.setPen(QColor(255, 0, 0))  # Red for weekends
        else:
            painter.setPen(QColor(0, 0, 0))  # Black for weekdays

        # Calculate font size and offsets based on cell dimensions
        font_size = min(rect.width(), rect.height()) // 5
        painter.setFont(QFont('Decorative', font_size))

        # Fetch the score from the database for the current date
        current_date = date.toPyDate().strftime('%Y-%m-%d')
        self.cursor.execute(f"SELECT score FROM score WHERE createdAt = '{current_date}'")
        results = self.cursor.fetchall()

        if results:
            total_score = sum(result[0] for result in results)
            average_score = total_score / len(results)
            rounded_average_score = round(average_score, 1)
            result = (rounded_average_score,)
        else:
            result = None


        # Determine the cell color
        if result is not None:
            cell_color = QColor(173, 216, 230)  # Light blue
        else:
            cell_color = QColor(192, 192, 192)  # Light gray

        # Fill the cell with the determined color
        painter.fillRect(rect, cell_color)

        # Draw a black border around the cell for today's date
        if date == QDate.currentDate():
            painter.setPen(QColor(0, 0, 0))  # Black for the border
            painter.drawRect(rect.adjusted(0, 0, -1, -1))  # Adjusted to avoid overlapping with other cells

        # Draw the date number with proportional offset and margin
        margin = 5  # Adjust the margin value as needed
        date_rect = QRectF(rect.left(), rect.top() + margin, rect.width(), rect.height() - 2 * margin)
        painter.setPen(QColor(0, 0, 0))  # Black for the date number
        painter.drawText(date_rect, Qt.AlignCenter, str(date.day()))

        # Draw the score below the date number with proportional offset
        if result is not None:
            score = result[0]
            text_rect = QRectF(rect.left(), rect.top() + 3 * font_size, rect.width(), rect.height() - 3 * font_size)
            painter.setPen(QColor(0, 0, 255))  # Blue for the score
            painter.drawText(text_rect, Qt.AlignCenter, f'{score}점')

        painter.restore()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = CalendarWidget()
    w.resize(800, 600)
    w.show()
    sys.exit(app.exec_())
