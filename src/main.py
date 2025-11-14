from PySide6.QtWidgets import QApplication
from config import Config
from ui.main_window import MainWindow
import sys

def main():
    app = QApplication(sys.argv)

    config = Config.load("config.yml")
    window = MainWindow(config)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
