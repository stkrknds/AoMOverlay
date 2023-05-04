import data
import gui
from pathlib import Path
from PyQt6.QtCore import QTimer

def update(_parser, window):
    if _parser.load_file() == _parser.fileLoaded:
        _game = data.create_game(_parser)
        window.viewData(_game)

def main():
    filePath = f"{Path.home()}/Documents/My Games/Age of Mythology/trigger2/trigtemp.xs"
    _parser = data.parser(filePath)

    app, window = gui.create_app_window()

    # create update tasks with 200ms timeout
    timer = QTimer()
    timer.timeout.connect(lambda: update(_parser, window))
    timer.setInterval(200)
    timer.start()

    # Start the event loop.
    app.exec()

if __name__ == '__main__':
    main()
