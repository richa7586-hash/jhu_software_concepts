from bs4 import BeautifulSoup
from urllib3 import request
from config import url, data_size

resp = request("GET", url)

html = resp.data.decode("utf-8")

soup = BeautifulSoup(html, 'html.parser')

print(soup.get)




