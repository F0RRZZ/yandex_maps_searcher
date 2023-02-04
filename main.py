import os
import sys
import requests

from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QMainWindow, QCheckBox
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import dotenv_values

config = {
    **dotenv_values(".env")
}
MAP_API_SERVER = 'https://static-maps.yandex.ru/1.x/'
GEOCODE_API_SERVER = "http://geocode-maps.yandex.ru/1.x/"


def get_coords(parametrs=None):
    if parametrs is None:
        parametrs = {}
    resp = requests.get(GEOCODE_API_SERVER, params=parametrs)
    json_resp = resp.json()
    coordinates = json_resp["response"]["GeoObjectCollection"]["featureMember"][0] \
        ["GeoObject"]["Point"]["pos"].split()
    return coordinates


def get_address(coords, postal_code):
    params = {
        "apikey": config['API_KEY'],
        "geocode": f"{coords[0]},{coords[1]}",
        "format": "json"
    }
    resp = requests.get(GEOCODE_API_SERVER, params=params)
    json_resp = resp.json()
    address = json_resp['response']['GeoObjectCollection']['featureMember'][0]['GeoObject']['metaDataProperty'] \
        ['GeocoderMetaData']['text']
    if not postal_code:
        return address
    params = {
        "apikey": config['API_KEY'],
        "geocode": address,
        "format": "json"
    }
    resp = requests.get(GEOCODE_API_SERVER, params=params)
    json_resp = resp.json()
    code = json_resp["response"]["GeoObjectCollection"]["featureMember"][0] \
        ["GeoObject"]["metaDataProperty"]["GeocoderMetaData"]['Address'] \
        ['postal_code']
    return address + ', ' + code


class MainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi('main_window.ui', self)
        self.setFixedSize(650, 450)

        self.press_delta = 20
        self.map_zoom = 5
        self.map_ll = [37.977751, 55.757718]
        self.point_coords = ''
        self.map_l = 'map'
        self.map_key = config['API_KEY']

        self.sat_btn.clicked.connect(self.set_map_show_mode)
        self.sch_btn.clicked.connect(self.set_map_show_mode)
        self.hyb_btn.clicked.connect(self.set_map_show_mode)
        self.search_btn.clicked.connect(self.search)
        self.reset_btn.clicked.connect(self.reset)

        self.refresh_map()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_PageUp and self.map_zoom < 17:
            self.map_zoom += 1
            self.press_delta /= 2
            self.refresh_map()
        if event.key() == Qt.Key_PageDown and self.map_zoom > 0:
            self.map_zoom -= 1
            self.press_delta *= 2
            self.refresh_map()
        if event.key() == Qt.Key_Up and self.map_ll[1] < 90:
            self.map_ll[1] += self.press_delta
            self.refresh_map()
        if event.key() == Qt.Key_Down and self.map_ll[1] > -90:
            self.map_ll[1] -= self.press_delta
            self.refresh_map()
        if event.key() == Qt.Key_Right:
            self.map_ll[0] = self.map_ll[0] + self.press_delta if self.map_ll[0] < 180 else -180
            self.refresh_map()
        if event.key() == Qt.Key_Left:
            self.map_ll[0] = self.map_ll[0] - self.press_delta if self.map_ll[0] > -180 else 180
            self.refresh_map()

    def set_map_show_mode(self):
        mode = self.sender().text()
        self.map_l = 'map' if mode == 'Схема' else 'sat' if mode == 'Спутник' else 'skl'
        self.refresh_map()

    def search(self):
        if not self.search_line.text():
            return
        params = {
            "apikey": config['API_KEY'],
            "geocode": self.search_line.text(),
            "format": "json"
        }
        coords = get_coords(params)
        self.map_ll = list(map(float, coords))
        self.address_lbl.setText(get_address(coords, self.index_cb.isChecked()))
        self.point_coords = f'{self.map_ll[0]},{self.map_ll[1]},pm2rdl'
        self.refresh_map()

    def reset(self):
        self.map_ll = [37.977751, 55.757718]
        self.point_coords = ''
        self.search_line.setText('')
        self.address_lbl.setText('')
        self.refresh_map()

    def refresh_map(self):
        params = {
            "z": self.map_zoom,
            "ll": f"{self.map_ll[0]},{self.map_ll[1]}",
            "l": self.map_l,
            "size": "650,450",
            "pt": self.point_coords
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
