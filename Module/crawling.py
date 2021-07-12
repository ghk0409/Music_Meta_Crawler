import pandas as pd
import requests
from bs4 import BeautifulSoup as bs
from bs4.element import NavigableString
import re

class crawler:
    '''
    Module for crawling meta data in URLs
    '''
    def __init__(self, headers, album_url, artist_url, music_url, outpath):
        self.headers = headers
        self.album_url = album_url
        self.artist_url = artist_url
        self.music_url = music_url
        self.outpath = outpath

############################################################################################################################
### album_url 파싱
############################################################################################################################

    def album_meta(self, album_id, idx, img_size=282):
        '''
        <params>
        album_url : str, album url for html parsing
        idx : int, album index => album cover image fileName
            ex) if idx = 12,
                - album idx = 12
                - album cover image fileName = 12.jpg
        img_size : int, image size to extract album cover image size

        <result>
        return df_result, artist_ids, song_ids

        df_result : dict, album meta data dictionary
        artist_ids : list, artist's id in Melon, multi layers
        song_ids : list, song's id in Melon, multi layers
        '''

        # 결과 저장 딕셔너리 생성
        result = {
            'album_id': album_id,
            'album_title': None,
            'artist_id': None,
            'album_artist': None,
            'album_cover': None,
            'album_cover_url': None,
            'album_date': None,
            'album_genre': None,
            'album_url': self.album_url,
        }

        ## 앨범 내 아티스트id와 음원id를 저장할 리스트 생성
        ## 앨범 참여 아티스트가 다수, 한 앨범에 여러 곡 있을 수 있기 때문
        artist_ids = []
        song_ids = []

        # album_url 파싱
        res_album = requests.get(self.album_url.format(album_id), headers=self.headers)
        source_album = res_album.text
        # html5lib을 이용할 경우에만 album_url 제대로 파싱 가능
        # lxml, html.parser 모두 안됨... 아마 웹브라우저와 같은 방식의 페이지 파싱 방식이 요구되는 듯
        soup_album = bs(source_album, 'html5lib')

        ## album meta data 추출 부분
        ## 1. 앨범명 추출
        album_title = soup_album.find('div', class_='song_name').text.replace('\n', '').replace('\t', '').replace('앨범명', '')
        result['album_title'] = album_title

        ## 2. 앨범 커버 추출 (default size = 282 x 282)
        album_cover = soup_album.find('a', id='d_album_org')
        img_url = album_cover.find('img')['src'].replace('/282/', f'/{img_size}/')
        ## 이미지 저장은 DB 구축된 후에
        # req.urlretrieve(img_url, self.outpath + f'{idx}.jpg')
        result['album_cover'] = idx
        result['album_cover_url'] = img_url

        ## 앨범 메타 데이터
        meta_album = soup_album.find('dl', class_='list')

        dt = meta_album.findAll('dt')
        dd = meta_album.findAll('dd')

        for i in range(len(dt)):
            ## 3. 앨범 발매일 추출
            if dt[i].text == '발매일':
                result['album_date'] = dd[i].text
            ## 4. 앨범 장르 추출 -> 여러 개일 경우 만들기
            if dt[i].text == '장르':
                result['album_genre'] = dd[i].text

        ## artist id 및 name 추출 부분
        div_artist = soup_album.find('div', class_='artist')
        artists = div_artist.findAll('a', class_='artist_name')
        artist_name = []

        ## artists가 존재하는 경우
        if artists:

            for a in artists:
                ## artist id 추출
                artist_href = a['href']
                artist_id = re.findall('\d+', artist_href)[0]
                artist_ids.append(artist_id)

                ## album artist 이름 추출
                name = a['title']
                artist_name.append(name)

        ## artists가 존재하지 않는 경우(ex. Various Artists)
        else:
            artist_name.append(div_artist.text.strip())

        result['artist_id'] = ', '.join(map(str, artist_ids))
        result['album_artist'] = ', '.join(map(str, artist_name))

        ## song id 추출 부분
        song_list = soup_album.find('div', class_='service_list_song d_song_list')
        tbody = song_list.find('tbody')
        tr = tbody.findAll('tr')

        ## music_url에 필요한 song id 추출
        for t in tr:
            song_href = t.find('a', class_='btn button_icons type03 song_info')

            if song_href:
                song_id = re.findall('\d+', song_href['href'])[0]
                #             print(song_id)
                song_ids.append(song_id)

        # 결과 저장 데이터프레임 생성
        df_result = pd.DataFrame([result])

        return df_result, artist_ids, song_ids


############################################################################################################################
### artist_url 파싱
############################################################################################################################

    def artist_meta(self, artist_ids, album_id, img_size=416):
        '''
        <params>
        artist_ids : list, artist's id for artist_url parsing
        album_id : int, album's id for distinct
        img_size : int, image size to extract artist cover image size

        <result>
        return df_result

        result : DataFrame, artist meta data DataFrame
        '''

        # 결과 저장 데이터프레임 생성
        df_result = pd.DataFrame()

        for idx in artist_ids:
            url = self.artist_url.format(idx)
            # 결과 저장 딕셔너리 생성
            result = {
                'artist_id': idx,
                'artist_name': None,
                'real_name': None,
                'type': None,
                'gender': None,
                'nation': None,
                'artist_url': url,
                'sim_artist': None,
                'agency_artist': None,
                'relate_artist': None,
                'affected_artist': None,
                'effected_artist': None,
                'artist_cover_url' : None,
            }

            # artist_url 파싱
            res_artist = requests.get(url, headers=self.headers)
            source_artist = res_artist.text
            soup_artist = bs(source_artist, 'html5lib')

            wrap_dtl_artist = soup_artist.find('div', class_='wrap_dtl_atist')
            ## 1. 아티스트명 추출
            artist_name = wrap_dtl_artist.find('p', class_='title_atist')  # .text.replace('아티스트명', '')
            remove_child_tags = [bs_object for bs_object in artist_name if isinstance(bs_object, NavigableString)]
            result['artist_name'] = remove_child_tags[0]

            ## 2. 실명이 따로 존재하는 경우
            real = wrap_dtl_artist.find('span', class_='realname')
            if real:
                real_name = re.sub('[()]', '', real.text.strip())
                result['real_name'] = real_name

            ## 3. 아티스트 이미지 url 추출
            artist_img = wrap_dtl_artist.find('span', class_='thumb')
            img_url = artist_img.find('img')['src'].replace('resize/416', f'resize/{img_size}')

            if 'default/noArtist' not in img_url:
                result['artist_cover_url'] = img_url

            ## 아티스트 성별, 유형 추출
            meta_artist = soup_artist.find('div', class_='section_atistinfo03')

            dt = meta_artist.findAll('dt')
            dd = meta_artist.findAll('dd')

            for i in range(len(dt)):
                ## 아티스트 유형, 성별 추출
                if dt[i].text == '유형':
                    type_gender = dd[i].text.replace('\n', '').replace('\t', '').split('|')

                    if len(type_gender) > 1:
                        ## 4. 유형
                        result['type'] = type_gender[0]
                        ## 5. 성별
                        result['gender'] = type_gender[1]
                    else:
                        ## 유형, 성별 중 1개만 나와있을 경우 유형/성별 파악
                        if type_gender[0] in ['솔로', '그룹']:
                            result['type'] = type_gender[0]
                        elif type_gender[0] in ['남성', '여성', '혼성']:
                            result['gender'] = type_gender[0]

            ######################################
            ## 우선 보류, 테이블 복잡도 등 원인
            ## 아티스트 그룹 확인
            #         group_check = meta_artist.find('div', class_='wrap_gmem')

            #         if group_check:
            #             print('그룹임')
            #         else:
            #             print('솔로임ㅋ')
            ######################################

            ## 6. 아티스트 국적 추출
            meta_artist = soup_artist.find('div', class_='section_atistinfo04')

            dt = meta_artist.findAll('dt')
            dd = meta_artist.findAll('dd')

            for i in range(len(dt)):
                ## 아티스트 국적있으면 추출
                if dt[i].text == '국적':
                    result['nation'] = dd[i].text

            ## 7. 연관 아티스트 추출 (5가지 수집)
            ## 유사 / 같은 소속사 / 관련 / 영향을 받은 / 영향을 준
            meta_rltn = soup_artist.find('div', class_='section_atistinfo06 d_artist_list')
            if meta_rltn:
                h4 = meta_rltn.findAll('h4', class_='title line arr')
                wrap_list = meta_rltn.findAll('div', class_='wrap_list')

                for i in range(len(h4)):
                    ## 유사 아티스트탭이 있을 경우에 해당 목록 전부 수집
                    if h4[i].text == '유사 아티스트':
                        sim_artists = []
                        thumb = wrap_list[i].findAll('a', class_='thumb')

                        for a in thumb:
                            sim_id = re.findall('\d+', a['href'])[0]
                            sim_artists.append(sim_id)

                        result['sim_artist'] = ', '.join(map(str, sim_artists))

                    ## 같은 소속사 아티스트탭이 있을 경우에 해당 목록 전부 수집
                    if h4[i].text == '같은 소속사 아티스트':
                        agency_artist = []
                        thumb = wrap_list[i].findAll('a', class_='thumb')

                        for a in thumb:
                            agency_id = re.findall('\d+', a['href'])[0]
                            agency_artist.append(agency_id)

                        result['agency_artist'] = ', '.join(map(str, agency_artist))

                    ## 관련 아티스트탭이 있을 경우에 해당 목록 전부 수집
                    if h4[i].text == '관련 아티스트':
                        relate_artist = []
                        thumb = wrap_list[i].findAll('a', class_='thumb')

                        for a in thumb:
                            relate_id = re.findall('\d+', a['href'])[0]
                            relate_artist.append(relate_id)

                        result['relate_artist'] = ', '.join(map(str, relate_artist))

                    ## 영향을 받은 아티스트탭이 있을 경우에 해당 목록 전부 수집
                    if h4[i].text == '영향을 받은 아티스트':
                        affected_artist = []
                        thumb = wrap_list[i].findAll('a', class_='thumb')

                        for a in thumb:
                            affected_id = re.findall('\d+', a['href'])[0]
                            affected_artist.append(affected_id)

                        result['affected_artist'] = ', '.join(map(str, affected_artist))

                    ## 영향을 준 아티스트탭이 있을 경우에 해당 목록 전부 수집
                    if h4[i].text == '영향을 준 아티스트':
                        effected_artist = []
                        thumb = wrap_list[i].findAll('a', class_='thumb')

                        for a in thumb:
                            effected_id = re.findall('\d+', a['href'])[0]
                            effected_artist.append(effected_id)

                        result['effected_artist'] = ', '.join(map(str, effected_artist))

            df = pd.DataFrame([result])
            df_result = pd.concat([df_result, df])

        return df_result


############################################################################################################################
### music_url 파싱
############################################################################################################################

    def song_meta(self, song_ids, album_id):
        '''
        <params>
        song_ids : list, song's id for artist_url parsing
        album_id : int, album's id for distinct

        <result>
        return df_result

        df_result : DataFrame, song meta data DataFrame
        '''

        # 결과 저장 데이터프레임 생성
        df_result = pd.DataFrame()

        for idx in song_ids:
            url = self.music_url.format(idx)
            # 결과 저장 딕셔너리 생성
            # check_adult는 0: 일반, 1: 19금곡
            result = {
                'album_id': album_id,
                'song_id': idx,
                'song_title': None,
                'artist_id': None,
                'artist_name': None,
                'genre': None,
                'lyrics': None,
                'composer_id': None,
                'composer': None,
                'lyricist_id': None,
                'lyricist': None,
                'arranger_id': None,
                'arranger': None,
                'check_adult': None,
                'song_url': url,
            }

            res_song = requests.get(url, headers=self.headers)
            source_song = res_song.text
            soup_song = bs(source_song, 'lxml')

            ## 1. 음원명 추출
            song_title = soup_song.find('div', class_='song_name').text.replace('\n', '').replace('\t', '').replace('곡명', '').strip()
            # 19금 음원의 경우 '19금'과 개행이 또 안에 있어서 제거
            result['song_title'] = song_title.replace('19금', '').strip()

            ## 2. 19세 음원 확인값
            if '19금' in song_title:
                result['check_adult'] = 1
            else:
                result['check_adult'] = 0

            ## 3. 아티스트 ID 추출
            div_artist = soup_song.find('div', class_='artist')
            song_artists = div_artist.findAll('a', class_='artist_name')
            artist_ids = []
            artist_names = []

            for artist in song_artists:
                artist_href = artist['href']
                artist_id = re.findall('\d+', artist_href)[0]
                artist_ids.append(artist_id)

                artist_name = artist['title']
                artist_names.append(artist_name)

            result['artist_id'] = ', '.join(map(str, artist_ids))
            result['artist_name'] = ', '.join(map(str, artist_names))

            ## 4. 음원 장르 추출
            meta_song = soup_song.find('div', class_='meta')

            dt = meta_song.findAll('dt')
            dd = meta_song.findAll('dd')

            for i in range(len(dt)):
                ## 음원 장르 추출 -> 여러 개일 경우 만들기
                if dt[i].text == '장르':
                    result['genre'] = dd[i].text

            ## 5. 음원 가사 추출
            lyrics = soup_song.find('div', class_='lyric')
            ## 가사 개행이 제대로 안돼서 야매로 개행 만들기
            lyrics = str(lyrics).replace('<div class="lyric" id="d_video_summary"><!-- height:auto; 로 변경시, 확장됨 -->',
                                         '').replace('</div>', '').replace('<br/>', '\n').strip()
            result['lyrics'] = lyrics

            ## 6. 음원 작사/작곡 추출
            prdcr = soup_song.find('div', class_='section_prdcr')
            ## prdcr 유무 판단 (없는 경우 존재하기 때문)
            if prdcr:
                a = prdcr.findAll('a', class_='artist_name')
                span = prdcr.findAll('span', class_='type')

                lyricist = []
                composer = []
                arranger = []

                lyricist_id = []
                composer_id = []
                arranger_id = []

                for i in range(len(a)):
                    ## 작사가, 작곡가, 편곡가 추출
                    if span[i].text == '작사':
                        lyricist.append(a[i].text)
                        href = a[i]['href']
                        idx = re.findall('\d+', href)[0]
                        lyricist_id.append(idx)

                    if span[i].text == '작곡':
                        composer.append(a[i].text)
                        href = a[i]['href']
                        idx = re.findall('\d+', href)[0]
                        composer_id.append(idx)

                    if span[i].text == '편곡':
                        arranger.append(a[i].text)
                        href = a[i]['href']
                        idx = re.findall('\d+', href)[0]
                        arranger_id.append(idx)

                result['lyricist'] = ', '.join(map(str, lyricist))
                result['composer'] = ', '.join(map(str, composer))
                result['arranger'] = ', '.join(map(str, arranger))

                result['lyricist_id'] = ', '.join(map(str, lyricist_id))
                result['composer_id'] = ', '.join(map(str, composer_id))
                result['arranger_id'] = ', '.join(map(str, arranger_id))

            df = pd.DataFrame([result])
            df_result = pd.concat([df_result, df])

        return df_result

############################################################################################################################


