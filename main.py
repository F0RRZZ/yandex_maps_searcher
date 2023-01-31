import os
import sys
import requests

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import dotenv_values


config = {
    **dotenv_values(".env")
}
MAP_API_SERVER = 'https://static-maps.yandex.ru/1.x/'


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('main_window.ui', self)
        self.setFixedSize(650, 450)

        self.press_delta = 24
        self.map_zoom = 5
        self.map_ll = [37.977751, 55.757718]
        self.map_l = 'map'
        self.map_key = config['API_KEY']

        self.refresh_map()

    def refresh_map(self):
        params = {
            "z": self.map_zoom,
            "ll": f"{self.map_ll[0]},{self.map_ll[1]}",
            "l": self.map_l,
            "size": "650,450"
        }
        session = requests.Session()
        retry = Retry(total=10, connect=5, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        response = session.get(MAP_API_SERVER, params=params)
        with open(file='map.png', mode='wb') as map_image:
            map_image.write(response.content)
        pixmap = QPixmap()
        pixmap.load('map.png')
        self.g_map.setPixmap(pixmap)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
