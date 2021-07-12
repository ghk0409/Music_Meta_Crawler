from .selenium_driver import webdriver_control
import re
import pandas as pd
from config import config

class music_crawler():
    # 클래스 초기화
    def __init__(self, chrome, music_idx, album_idx):
        self.music_idx = music_idx
        self.album_idx = album_idx
        self.music_url = config.default_urls['music_url'].format(self.music_idx)
        self.chrome = webdriver_control.parsing_chrome(chrome, self.music_url)

    # 음원 타이틀 추출
    def extract_music_title(self):
        music_title = self.chrome.find_element_by_css_selector('#downloadfrm > div > div > div.entry > div.info > div.song_name').text
        return music_title

    # 음원 성인곡 유무 체크
    def extract_19_music(self):
        age_19 = self.chrome.find_elements_by_class_name('age_19')
        if age_19:
            check_adult = 1
        else:
            check_adult = 0

        return check_adult

    # 음원 아티스트명 및 idx 추출
    def extract_music_artist(self):
        # 아티스트 정보가 없을 경우 (Various Artists) 대비
        artist_idx = None
        artist_name = None

        artist_data = self.chrome.find_elements_by_xpath('//*[@id="downloadfrm"]/div/div/div/div/div/a')
        # 아티스트 정보가 있을 경우
        if artist_data:
            idx = []
            name = []
            # 아티스트가 여러 명일 수 있음
            for artist in artist_data:
                name.append(artist.text)
                idx.append(re.findall('\d+', artist.get_attribute('href'))[0])
            # 데이터프레임에 보기 좋게 넣기 위함(csv 파일 활용 용도)
            artist_idx = ', '.join(map(str, idx))
            artist_name = ', '.join(map(str, name))

        return artist_idx, artist_name

    # 음원 장르 추출
    def extract_music_genre(self):
        dt = self.chrome.find_elements_by_xpath('//*[@id="downloadfrm"]/div/div/div[2]/div[2]/dl/dt')
        dd = self.chrome.find_elements_by_xpath('//*[@id="downloadfrm"]/div/div/div[2]/div[2]/dl/dd')

        for i in range(len(dt)):
            ## 장르있으면 추출 (멜론은 장르 다 있음)
            if dt[i].text == '장르':
                music_genre = dd[i].text
                break

        return music_genre

    # 음원 가사 추출
    def extract_music_lyric(self):
        # 가사 없는 경우 존재
        music_lyric = None

        lyric = self.chrome.find_elements_by_xpath('//*[@id="d_video_summary"]')
        # 가사 존재할 경우
        if lyric:
            music_lyric = lyric[0].text

        return music_lyric

    # 작사 / 작곡 / 편곡가 이름 및 idx 추출
    def extract_music_producer(self):
        prdcr = self.chrome.find_elements_by_xpath('//*[@id="conts"]/div[3]/ul/li/div/div/a')
        prdcr_idx = self.chrome.find_elements_by_xpath('//*[@id="conts"]/div[3]/ul/li/div/div/span')

        lyricist = []
        composer = []
        arranger = []

        lyricist_idx = []
        composer_idx = []
        arranger_idx = []

        for i in range(len(prdcr)):
            if prdcr_idx[i].text == '작사':
                lyricist.append(prdcr[i].text)
                lyricist_idx.append(re.findall('\d+', prdcr[i].get_attribute('href'))[0])
            if prdcr_idx[i].text == '작곡':
                composer.append(prdcr[i].text)
                composer_idx.append(re.findall('\d+', prdcr[i].get_attribute('href'))[0])
            if prdcr_idx[i].text == '편곡':
                arranger.append(prdcr[i].text)
                arranger_idx.append(re.findall('\d+', prdcr[i].get_attribute('href'))[0])

        # 결과값이 많아서 dict로 변환
        result = {
            'lyricist': ', '.join(map(str, lyricist)),
            'lyricist_idx': ', '.join(map(str, lyricist_idx)),
            'composer': ', '.join(map(str, composer)),
            'composer_idx': ', '.join(map(str, composer_idx)),
            'arranger': ', '.join(map(str, arranger)),
            'arranger_idx': ', '.join(map(str, arranger_idx)),
        }

        return result

    # 데이터프레임 결과 반환
    def return_result(self):
        music_title = self.extract_music_title()
        check_adult = self.extract_19_music()
        artist_idx, artist_name = self.extract_music_artist()
        music_genre = self.extract_music_genre()
        music_lyric = self.extract_music_lyric()
        music_producer = self.extract_music_producer()


        meta_music_ = {
            'album_id': self.album_idx,
            'song_id': self.music_idx,
            'song_title': music_title,
            'artist_id': artist_idx,
            'artist_name': artist_name,
            'genre': music_genre,
            'lyrics': music_lyric,
            'composer_id': music_producer['composer_idx'],
            'composer': music_producer['composer'],
            'lyricist_id': music_producer['lyricist_idx'],
            'lyricist': music_producer['lyricist'],
            'arranger_id': music_producer['arranger_idx'],
            'arranger': music_producer['arranger'],
            'check_adult': check_adult,
            'song_url': self.music_url,
        }

        df_result = pd.DataFrame([meta_music_])

        return df_result