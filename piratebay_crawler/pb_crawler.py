from bs4 import BeautifulSoup as bs
from selenium import webdriver
import re
import requests
from hurry.filesize import filesize
import chromedriver_binary

chrome_options=webdriver.ChromeOptions()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
# chrome_options.add_argument("window-size=1400,2100")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(chrome_options=chrome_options)
piratebay_url="https://proxybay.github.io/"


def crawl(url):
    magnet_url = []
    magnet_title = []
    magnet_size = []
    req = requests.get(piratebay_url)
    soup = bs(req.content, 'lxml')
    res = soup.select('a.t1')
    message=f"Results from {res[0]['href']} \n\n"
    driver.get(res[0]['href'] + '/search.php?q=' + '+'.join(url))
    soup = bs(driver.page_source, 'lxml')
    for tag in soup.findAll(href=re.compile("/description.php"))[0:5]:
        print(tag.string)
        magnet_title.append(tag.string)
    for tag in soup.findAll(href=re.compile("magnet:"))[0:5]:
        print(tag)
        magnet_url.append(tag['href'])
    for tag in soup.select('span.item-size>input')[0:5]:
        magnet_size.append(filesize.size(int(tag['value'])))
    for item in magnet_url:
        message += f"\n\n<b><u>{magnet_title[magnet_url.index(item)]}({magnet_size[magnet_url.index(item)]})</u></b>\n" \
                   f"{item}"
    return message