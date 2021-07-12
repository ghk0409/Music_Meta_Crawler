from .selenium_driver import webdriver_control
from bs4 import BeautifulSoup as bs
from bs4.element import NavigableString
import re
import pandas as pd
from config import config

class artist_crawler():
    # 클래스 초기화
    def __init__(self, chrome, artist_idx):
        self.artist_idx = artist_idx
        self.artist_url = config.default_urls['artist_url'].format(self.artist_idx)
        self.chrome = webdriver_control.parsing_chrome(chrome, self.artist_url)

    # 아티스트명(활동명) 및 실명 추출
    def extract_artist_name(self):
        title_artist = self.chrome.find_element_by_class_name('title_atist')
        title_artist_html = bs(title_artist.get_attribute('innerHTML'), 'html.parser')
        remove_child_tags = [bs_object for bs_object in title_artist_html if isinstance(bs_object, NavigableString)]

        return remove_child_tags[0]

    # 아티스트 실명 추출
    def extract_artist_real_name(self):
        real_name = None
        real = self.chrome.find_elements_by_class_name('realname')
        if real:
            real_name = re.sub('[()]', '', real[0].text.strip())

        return real_name

    # 아티스트 커버 URL 추출
    def extract_artist_cover(self, img_size=416):
        xpath_cover = self.chrome.find_element_by_xpath('//*[@id="artistImgArea"]/img')
        artist_cover = xpath_cover.get_attribute('src').replace('resize/416', f'resize/{img_size}')
        return artist_cover

    # 아티스트 유형 및 성별 추출
    def extract_artist_gender_type(self):
        artist_gender = None
        artist_type = None

        section3 = self.chrome.find_elements_by_class_name('section_atistinfo03')[0]
        dt = section3.find_elements_by_xpath('dl/dt')
        dd = section3.find_elements_by_xpath('dl/dd')

        for i in range(len(dt)):
            ## 아티스트 유형, 성별 추출
            if dt[i].text == '유형':
                type_gender = dd[i].text.split(' |')

                if len(type_gender) > 1:
                    ## 유형
                    artist_type = type_gender[0]
                    ## 성별
                    artist_gender = type_gender[1]
                else:
                    ## 유형, 성별 중 1개만 나와있을 경우 유형/성별 파악
                    if type_gender[0] in ['솔로', '그룹']:
                        artist_type = type_gender[0]
                    elif type_gender[0] in ['남성', '여성', '혼성']:
                        artist_gender = type_gender[0]
                break

        return artist_gender, artist_type

    # 아티스트 국적 추출
    def extract_artist_nation(self):
        artist_nation = None

        section4 = self.chrome.find_elements_by_class_name('section_atistinfo04')[0]
        dt = section4.find_elements_by_xpath('dl/dt')
        dd = section4.find_elements_by_xpath('dl/dd')

        for i in range(len(dt)):
            ## 아티스트 국적있으면 추출
            if dt[i].text == '국적':
                artist_nation = dd[i].text
                break

        return artist_nation

    # 연관 아티스트 추출
    def extract_artist_relation(self):
        relate_artist = None
        sim_artist = None
        agency_artist = None
        affected_artist = None
        effected_artist = None

        section6 = self.chrome.find_elements_by_class_name('section_atistinfo06')

        if section6:
            wrap_rltn = section6[0].find_elements_by_class_name('wrap_rltn')

            for wrap in wrap_rltn:
                h4 = wrap.find_element_by_css_selector('h4').text

                if h4 == '관련 아티스트':
                    relate_artist = []
                    thumb = wrap.find_elements_by_class_name('thumb')

                    for t in thumb:
                        idx = re.findall('\d+', t.get_attribute('href'))[0]
                        relate_artist.append(idx)

                elif h4 == '유사 아티스트':
                    sim_artist = []
                    thumb = wrap.find_elements_by_class_name('thumb')

                    for t in thumb:
                        idx = re.findall('\d+', t.get_attribute('href'))[0]
                        sim_artist.append(idx)

                elif h4 == '같은 소속사 아티스트':
                    agency_artist = []
                    thumb = wrap.find_elements_by_class_name('thumb')

                    for t in thumb:
                        idx = re.findall('\d+', t.get_attribute('href'))[0]
                        agency_artist.append(idx)

                elif h4 == '영향을 받은 아티스트':
                    affected_artist = []
                    thumb = wrap.find_elements_by_class_name('thumb')

                    for t in thumb:
                        idx = re.findall('\d+', t.get_attribute('href'))[0]
                        affected_artist.append(idx)

                elif h4 == '영향을 준 아티스트':
                    effected_artist = []
                    thumb = wrap.find_elements_by_class_name('thumb')

                    for t in thumb:
                        idx = re.findall('\d+', t.get_attribute('href'))[0]
                        effected_artist.append(idx)

        return relate_artist, sim_artist, agency_artist, affected_artist, effected_artist

    # 데이터프레임 결과 반환
    def return_result(self):
        artist_name = self.extract_artist_name()
        artist_real_name = self.extract_artist_real_name()
        artist_cover = self.extract_artist_cover()
        artist_gender, artist_type = self.extract_artist_gender_type()
        artist_nation = self.extract_artist_nation()
        relate_artist, sim_artist, agency_artist, affected_artist, effected_artist = \
            self.extract_artist_relation()


        meta_artist_ = {
            'artist_id': self.artist_idx,
            'artist_name': artist_name,
            'real_name': artist_real_name,
            'type': artist_type,
            'gender': artist_gender,
            'nation': artist_nation,
            'artist_url': self.artist_url,
            'sim_artist': ', '.join(map(str, sim_artist)),
            'agency_artist': ', '.join(map(str, agency_artist)),
            'relate_artist': ', '.join(map(str, relate_artist)),
            'affected_artist': ', '.join(map(str, affected_artist)),
            'effected_artist': ', '.join(map(str, effected_artist)),
            'artist_cover_url' : ', '.join(map(str, artist_cover)),
        }

        df_result = pd.DataFrame([meta_artist_])

        return df_result