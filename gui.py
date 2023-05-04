from PyQt6.QtCore import QPoint, QPointF, Qt, QSize, QSettings
from PyQt6.QtWidgets import QApplication, QBoxLayout, QLabel, QMainWindow, QHBoxLayout, QWidget, QGridLayout
from PyQt6.QtGui import QColor, QFont, QPainter, QPixmap, QBrush, QRadialGradient, QIcon, QFontDatabase
import os.path
import sys

# Thats for pyinstaller to include the images correctly.
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PlayerFrame(QWidget):
    def __init__(self, player) -> None:
        super().__init__()
        # the side of the window, that the playerframe will be placed on
        self.LeftSide, self.RightSide = 0, 1
        side = player.team
        # the alignment and the placemenet order depend on the side
        if side == self.RightSide:
            self.alignment = Qt.AlignmentFlag.AlignRight
            boxPlaceDir = QBoxLayout.Direction.RightToLeft
        else:
            self.alignment = Qt.AlignmentFlag.AlignLeft
            boxPlaceDir = QBoxLayout.Direction.LeftToRight

        # convert float values to int(%)
        percentRGB = list(map(lambda x: x*100, player.color))

        # top level layout (God Image + grid)
        topLayout = QHBoxLayout()
        topLayout.setSpacing(3)
        topLayout.setContentsMargins(0, 0, 0, 0)
        topLayout.setDirection(boxPlaceDir)

        godImage = QLabel()
        godImage.setPixmap(QPixmap(resource_path(f"icons/{player.god}.png")))

        if player.streak >= 0:
            winsString = f"{player.wins}(+{player.streak})W"
            lossesString = f"{player.losses}L"
        else:
            winsString = f"{player.wins}W"
            lossesString = f"{player.losses}({player.streak})L"

        
        playerName = QLabel(f"{player.name}")
        # assign player color
        playerName.setStyleSheet(f"color: rgb({percentRGB[0]}%, {percentRGB[1]}%, {percentRGB[2]}%);")
        playerRank = QLabel(f"#{player.rank}")
        playerElo = QLabel(f"{player.rating}")
        playerWins = QLabel(winsString)
        playerWins.setStyleSheet("color: green")
        PlayerLosses = QLabel(lossesString)
        PlayerLosses.setStyleSheet("color: red")
        playerWinRatio = QLabel(f"{player.winRatio}%")

        grid = QGridLayout()
        grid.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        grid.setVerticalSpacing(0)
        grid.setHorizontalSpacing(3)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(playerName, 0, 0, 1, 5, alignment=self.alignment)
        grid.addWidget(playerRank, 1, 0, alignment=self.alignment)
        grid.addWidget(playerElo, 1, 1, alignment=self.alignment)
        grid.addWidget(playerWins, 1, 2, alignment=self.alignment)
        grid.addWidget(PlayerLosses, 1, 3, alignment=self.alignment)
        grid.addWidget(playerWinRatio, 1, 4, alignment=self.alignment)

        topLayout.addWidget(godImage)
        topLayout.addLayout(grid)
        topLayout.addStretch()

        self.setLayout(topLayout)

class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.settings = QSettings('AomOverlay', 'AomOverlay')
        # Initial window size/pos last saved. Use default values for first time
        self.resize(self.settings.value("size", QSize(800, 32)))
        self.move(self.settings.value("pos", QPoint(50, 50)))

        self.setContentsMargins(0, 0, 0, 0)
        self.setWindowTitle("AoM Overlay")
        self.setWindowIcon(QIcon(resource_path("icons/Thor.png")))
        self.setFixedHeight(32)
        self.setMinimumWidth(700)
        self.setMouseTracking(True)
        # make transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)

        self.mousePos = None
        self.mousePressed = False
        self.isResizeLeft = False
        self.isResizeRight = False
        self.initialWidth =  None

    def paintEvent(self, event):
        qp = QPainter(self)
        self.drawGradient(qp, event)

    def drawGradient(self, qp, event):
        grad = QRadialGradient(QPointF(event.rect().width() / 2, event.rect().height() / 2), (event.rect().width()/2 - 270))

        grad.setColorAt(0, QColor.fromRgbF(0, 0, 0, 0))
        grad.setColorAt(0.5, QColor.fromRgbF(0, 0, 0, 0))
        grad.setColorAt(0.85, QColor.fromRgbF(0, 0, 0, 0))
        grad.setColorAt(0.9, QColor.fromRgbF(0, 0, 0, 0.6))
        grad.setColorAt(1, QColor.fromRgbF(0, 0, 0, 0.75))

        qp.fillRect(event.rect(), QBrush(grad))

    def viewData(self, game):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        playerFrame1 = PlayerFrame(game.playersList[0][0])
        playerFrame2 = PlayerFrame(game.playersList[1][0])
        layout.addWidget(playerFrame1)
        layout.addWidget(playerFrame2)

        widget = QWidget()
        widget.setContentsMargins(0,0,0,0)
        widget.setLayout(layout)
        widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setCentralWidget(widget)

    def resizeRight(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), self.initialWidth + delta.x())
        window.resize(width, window.height())

    def resizeLeft(self, delta):
        window = self.window()
        width = max(window.minimumWidth(), window.width() - delta.x())
        geo = window.geometry()
        geo.setLeft(geo.right() - width + 1)
        window.setGeometry(geo)

    def mousePressEvent(self, event):
        window = self.window()
        if event.button() == Qt.MouseButton.LeftButton:
            self.mousePressed = True
            self.mousePos = event.pos()
            if self.mousePos.x() < 10:
                self.isResizeLeft = True
                self.isResizeRight = False
            elif self.mousePos.x() > self.width() - 10:
                self.isResizeLeft = False
                self.isResizeRight = True
                self.initialWidth =  window.width()
            else:
                self.setCursor(Qt.CursorShape.SizeAllCursor)
                self.isResizeLeft = False
                self.isResizeRight = False

    def mouseMoveEvent(self, event):
        curMousePos = event.pos()
        if not self.mousePressed:
            if curMousePos.x() < 10 or curMousePos.x() > self.width() - 10:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
            else:
                self.unsetCursor()

        if self.mousePos is not None:
            delta = event.pos() - self.mousePos
            if self.isResizeLeft:
                self.resizeLeft(delta)
            elif self.isResizeRight:
                self.resizeRight(delta)
            else:
                self.move(self.x() + delta.x(), self.y() + delta.y())

    def mouseReleaseEvent(self, event):
        self.isResizeRight = False
        self.isResizeLeft = False
        self.mousePos = None
        self.mousePressed = False
        if event.pos().x() > 10 and event.pos().x() < self.width() - 10:
            self.unsetCursor()
        self.initialWidth = self.width()

    def closeEvent(self, event):
        # Write window size and position to config file
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        event.accept()

def create_app_window():
    app = QApplication([])
    app.setStyleSheet('QLabel{color: white;}')
    # load fonts
    id = QFontDatabase.addApplicationFont(resource_path("fonts/Ubuntu-Bold.ttf"))
    families = QFontDatabase.applicationFontFamilies(id)
    cfont = QFont(families[0], pointSize=11, weight=QFont.Weight.Bold)
    app.setFont(cfont, "QLabel")

    window = MainWindow()
    window.show()

    return app, window
