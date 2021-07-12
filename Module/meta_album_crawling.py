from .selenium_driver import webdriver_control
import re
import pandas as pd
from config import config

class album_crawler():
    # 클래스 초기화
    def __init__(self, chrome, album_idx):
        self.album_idx = album_idx
        self.album_url = config.default_urls['album_url'].format(self.album_idx)
        self.chrome = webdriver_control.parsing_chrome(chrome, self.album_url)

    # 앨범 타이틀 추출
    def extract_album_title(self):
        xpath_title = self.chrome.find_element_by_xpath('//*[@id="conts"]/div[2]/div/div[2]/div[1]/div[1]')
        album_title = xpath_title.text
        return album_title

    # 앨범 커버 URL 추출 (default size = 282 x 282)
    def extract_album_cover(self, img_size=282):
        xpath_cover = self.chrome.find_elements_by_xpath('//*[@id="d_album_org"]/img')
        album_cover = xpath_cover[0].get_attribute('src').replace('/282/', f'/{img_size}/')
        return album_cover

    # 앨범 발매일 추출
    def extract_album_date(self):
        album_date = self.chrome.find_element_by_xpath('//*[@id="conts"]/div[2]/div/div[2]/div[2]/dl/dd[1]').text
        return album_date

    # 앨범 장르 추출
    def extract_album_genre(self):
        album_genre = self.chrome.find_element_by_xpath('//*[@id="conts"]/div[2]/div/div[2]/div[2]/dl/dd[2]').text
        return album_genre

    # 앨범 아티스트명과 아티스트 idx 추출 (meta_artist_crawling을 위한 아티스트 idx)
    def extract_album_artists(self):
        # 앨범 아티스트 이름 및 idx
        xpath_artists = self.chrome.find_elements_by_xpath('//*[@id="conts"]/div[2]/div/div[2]/div[1]/div[2]/a')

        artist_name = []
        artist_idx = []

        # 아티스트가 존재할 경우
        if xpath_artists:
            for artist in xpath_artists:
                artist_name.append(artist.text)
                artist_idx.append(re.findall('\d+', artist.get_attribute('href'))[-1])
        # 아티스트가 존재하지 않을 경우 0으로 처리 (ex. Various Artists)
        else:
            artist_name.append(self.chrome.find_element_by_xpath('//*[@id="conts"]/div[2]/div/div[2]/div[1]/div[2]').text)
            artist_idx.append(0)

        return artist_idx, artist_name

    # 앨범 수록 음원들의 idx 추출 (meta_music_crawling을 위한 음원 idx)
    def extract_album_musics(self):
        xpath_musics = self.chrome.find_elements_by_xpath('//*[@id="frm"]/div/table/tbody/tr/td/div/a')

        music_idxes = []
        for music in xpath_musics:
            music_idx = re.findall('\d+', music.get_attribute('href'))[-1]
            music_idxes.append(music_idx)

        return music_idxes

    # 데이터프레임 결과 반환
    def return_result(self):
        album_title = self.extract_album_title()
        album_cover = self.extract_album_cover()
        album_date = self.extract_album_date()
        album_genre = self.extract_album_genre()
        artist_idx, artist_name = self.extract_album_artists()
        album_musics = self.extract_album_musics()

        artist_idx_comma = ', '.join(map(str, artist_idx))
        artist_name_comma = ', '.join(map(str, artist_name))

        meta_album_ = {
            'album_id' : self.album_idx,
            'album_title' : album_title,
            'album_date' : album_date,
            'album_genre' : album_genre,
            'artist_id' : artist_idx_comma,
            'album_artist' : artist_name_comma,
            'album_cover_url': album_cover,
            'album_url': self.album_url,
        }

        df_result = pd.DataFrame([meta_album_])

        return df_result, artist_idx, album_musics