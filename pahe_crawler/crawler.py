from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import chromedriver_binary

chrome_options=webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("window-size=100,100")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("user-agent=Mozilla/5.0 (compatible; MSIE 9.0; Windows Phone OS 7.5; Trident/5.0; IEMobile/9.0)")
driver = webdriver.Chrome(chrome_options=chrome_options)
pahe_url = "https://pahe.ph/"
print("Agent ",driver.execute_script("return navigator.userAgent"))

class Crawler:
    search_results = bs()

    def find_movies(self, url):
        driver.get(pahe_url + '?s=' + '+'.join(url))
        soup = bs(driver.page_source, 'lxml')
        Crawler.search_results = soup.select('.timeline-content')
        return soup.select('.timeline-content')

    def select_movie(self, index):
        driver.get(Crawler.search_results[int(index)].select('.post-box-title>a')[0]['href'])
        soup = bs(driver.page_source, 'lxml')
        download_box = soup.select('.box-inner-block')
        download_map = {'movies': []}
        series_box = soup.findAll('div', 'post-tabs-ver')
        series = {'series': []}
        if len(series_box) > 0:
            count = 0
            for tags in series_box:
                for tag in tags:
                    if tag.name == "ul":
                        count += 1
                        series['series'].append({count: []})
                        for episode_tag in tag:
                            print(episode_tag.string)
                            series['series'][count - 1][count].append(episode_tag.string)
            else:
                print(series)
                return series
        else:
            for tags in download_box:
                if tags != "\n":
                    download_map['movies'].append(tags)
            return download_map

    def select_series_option(self, div, li):
        print(div, li)
        xpath = f'(//ul[@class="tabs-nav"])[{div}]/li[{li}]'
        driver.find_element_by_xpath(xpath).click()
        soup = bs(driver.page_source, 'lxml')
        hosts = soup.findAll('div', 'post-tabs-ver')
        Crawler.cleanup(self)
        return {div: {li: hosts[int(div) - 1].select('.pane')}}

    def select_file_host(self, option, **kwargs):
        if 'div' in kwargs:
            print("inside")
            xpath = f'//div[@class="post-tabs-ver"][{kwargs.get("div")}]//div[{kwargs.get("li")}]//div[{kwargs.get("box_inner_block")}]//*[{option}]'
            print(xpath)
            ele = driver.find_element_by_xpath(xpath)
            print("element", ele.tag_name, ele.text)
            ele.click()
            Crawler.cleanup(self)
        else:
            xpath = f'(//div[@class="box-inner-block"])[{kwargs.get("box_inner_block")}]//*[{option}]'
            print(xpath)
            driver.find_element_by_xpath(xpath).click()
            print("Started")
            print("Redirected to link generation")
            Crawler.cleanup(self)
        try:
            agreement_ele = WebDriverWait(driver, 5).until(
                (EC.element_to_be_clickable((By.CLASS_NAME, 'css-1hy2vtq'))))
            print("Trying to skip agreements")
            agreement_ele.click()
            agree_ele = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'qc-cmp2-hide-desktop')))
            agree_ele.click()
            print("Success")
        except:
            print("No agreement")
        print(driver.title)
        ele = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//div[@class="wait"]/center/img')))
        print(ele.tag_name)
        ele.click()
        print("Started link generation")
        try:
            agreement_ele = WebDriverWait(driver, 5).until(
                (EC.element_to_be_clickable((By.CLASS_NAME, 'css-1hy2vtq'))))
            print("Trying to skip agreements")
            agreement_ele.click()
            agree_ele = WebDriverWait(driver, 2).until(
                EC.element_to_be_clickable((By.CLASS_NAME, 'qc-cmp2-hide-desktop')))
            agree_ele.click()
            print("Success")
        except:
            print("No agreement")
        ele = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'generater')))
        ele.click()
        print("Link generated")
        ele = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, 'showlink')))
        ele.click()
        print("Getting download link ready")
        print(driver.title)
        driver.switch_to.window(driver.window_handles[1])
        print(driver.title)
        soup = bs(driver.page_source, 'lxml')
        print("All done!")
        page=bs(driver.page_source,'lxml')
        print(page.prettify())
        ele = WebDriverWait(driver, 20).until(EC.visibility_of_element_located((By.CLASS_NAME, 'btn-primary')))
        driver.set_page_load_timeout(10)
        driver.execute_script('arguments[0].click();', ele)
        driver.switch_to.window(driver.window_handles[1])
        print(driver.current_url)
        file_url = driver.current_url
        print(soup.select('.btn.btn-primary.btn-xs')[0]['href'])
        return file_url

    def cleanup(self):
        for tab in driver.window_handles[1:]:
            driver.switch_to.window(tab)
            driver.close()
        else:
            driver.switch_to.window(driver.window_handles[0])
            print("cleaned up all unwanted tags")

# c=Crawler()
# c.find_movies(['loki'])
# # choice=int(input("select one :"))
# c.select_movie(0)
# option=int(input("Option:"))
# c.select_file_host(option)
