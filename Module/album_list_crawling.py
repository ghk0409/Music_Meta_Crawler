import pandas  as pd
import re
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from config import config
import time

# type 파라미터 값 확인 처리 에러
class GenreTypeError(Exception):
    def __init__(self):
        super().__init__('장르 타입 구분을 위해 [0, 1, 2] 중에서 선택해주세요.')

# type - genre 파라미터 값 확인 처리 에러
class GenreClassError(Exception):
    def __init__(self):
        super().__init__('해당 타입(type)에 장르(genre)가 포함되어 있지 않습니다. 확인해주세요.')

# classic 장르의 경우 date 파라미터 값 확인 처리 에러
class ClassicReferenceDateError(Exception):
    def __init__(self):
        super().__init__('Classic 장르 앨범 수집에 필요한 기준 날짜 필요 [ex.2021.01.01]')

# type - genre 체크를 위한 메서드
def check_type_genre(type, genre):
    if type == 0:
        genre_keys = config.nation_korea.keys()
    elif type == 1:
        genre_keys = config.nation_overseas.keys()
    else:
        genre_keys = config.nation_etc.keys()

    if genre in genre_keys:
        return True
    else:
        return False

class album_list_crawler:
    # 클래스 초기화
    def __init__(self, chrome, type:int, genre:str, date=None, page = 10):
        # type이 0, 1, 2가 아닌 값이 들어왔을 경우 예외 발생
        if type > 2:
            raise GenreTypeError
        # type에 존재하지 않는 genre를 입력 받았을 경우 예외 발생
        if not check_type_genre(type, genre):
            raise GenreClassError
        # classic 장르를 받고 date 값을 받지 않았을 경우 예외 발생
        if genre == 'classic' and date is None:
            raise ClassicReferenceDateError

        self.chrome = chrome
        self.genre = genre
        self.type = type
        self.date = date
        self.page = page

    # 앨범 리스트 추출
    def extract_album_list(self):
        # 파싱 url 설정
        # 국내 장르
        if self.type == 0:
            self.url = config.nation_korea[self.genre]
        # 해외 장르
        elif self.type == 1:
            self.url = config.nation_overseas[self.genre]
        # 그외 장르
        elif self.type == 2:
            self.url = config.nation_etc[self.genre]

        # 장르가 'classic'일 경우, 최신 앨범 탭에서 추출 진행
        if self.genre == 'classic':
            start_idx = 1
            check = True
            new_album_idx = []

            while check:
                album_list_url = self.url.format(start_idx)
                self.chrome.get(album_list_url)
                time.sleep(1)

                entry = self.chrome.find_elements_by_css_selector('#frm > div > ul > li > div.entry')

                for i, album in enumerate(entry):
                    # 앨범 발매일 기준 (기준 발매일 이후 데이터 수집)
                    reg_date = album.find_element_by_css_selector('span.reg_date').text
                    if reg_date > self.date:
                        href = album.find_element_by_css_selector('div > a').get_attribute('href')
                        album_idx = re.findall('\d+', href)[-1]
                        new_album_idx.append(album_idx)

                    # 앨범 발매일 기준 이전일 경우 중단
                    else:
                        check = False
                        break

                start_idx += 20

        else:
            # 앨범 목록 수집 모듈
            start_idx = 1
            new_album_idx = []

            while start_idx < self.page*50:
                album_list_url = self.url.format(start_idx)
                self.chrome.get(album_list_url)
                time.sleep(1)

                album_list = self.chrome.find_elements_by_css_selector(
                    '#frm > div > table > tbody > tr > td > div > a.image_typeAll')

                for i, album in enumerate(album_list):
                    href = album.get_attribute('href')
                    album_idx = re.findall('\d+', href)[-1]
                    new_album_idx.append(album_idx)

                start_idx += 50

        return new_album_idx