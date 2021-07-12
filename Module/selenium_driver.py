from selenium import webdriver
from selenium.webdriver.chrome.options import Options

class webdriver_control:
    # selenium webdriver (chrome) 설정
    def generate_chrome(driver_path: str, ) -> webdriver:
        # 크롬 웹드라이버 옵션 설정
        options = Options()
        options.add_argument('--remote-debugging-port=9222')
        options.add_argument('--user-data-dir=C:/Chrome_debug_temp')
        options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")

        chrome = webdriver.Chrome(executable_path=driver_path, options=options)

        return chrome

    # selenium url 파싱 결과 반환
    def parsing_chrome(chrome: webdriver, url,):
        chrome.get(url)
        return chrome

    # webdriver 종료
    def close_chrome(chrome: webdriver):
        def close():
            chrome.close()

        return close

