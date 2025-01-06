import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import random
from PIL import Image
from io import BytesIO

# Configure requests to use Tor
proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

def fetch_image_urls(url):
    response = requests.get(url, proxies=proxies)
    soup = BeautifulSoup(response.text, 'html.parser')
    img_tags = soup.find_all('img')
    img_urls = []
    next_url = ''
    
    for img in img_tags:
        if 'src' in img.attrs:
            img_url = urljoin(url, img['src'])
            img_response = requests.get(img_url, proxies=proxies)
            img_obj = Image.open(BytesIO(img_response.content))
            if img_obj.width >= 300 and img_obj.height >= 300:
                img_urls.append(img_url)
    
    print(f"img_urls: {img_urls}")
    
    # Find the next page URL
    next_page_tags = soup.find_all('a')
    next_page_url_array = []
    print(f"next_page_tags : {next_page_tags}")
    for next_page_tag in next_page_tags:
        print(f"next_page_tag : {next_page_tag}")
        if 'href' in next_page_tag.attrs:
            next_page_url = urljoin(url, next_page_tag['href'])
            next_page_url_array.append(next_page_url)
    print(f"next_page_url_array: {next_page_url_array}")
    next_url = next_page_url_array[random.randint(0, len(next_page_url_array) - 1)]
    print(f"next_url: {next_url}")
    return img_urls,next_url

def download_images(img_urls, folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    for img_url in img_urls:
        img_name = os.path.join(folder_path, img_url.split('/')[-1])
        with open(img_name, 'wb') as img_file:
            img_file.write(requests.get(img_url, proxies=proxies).content)

def main(target_url):
    if len(target_url) != 0:
        print(f"Downloading images from {target_url}")
        web_url = target_url  # Replace with the target URL
        folder_path = './downloaded_images'
        folder_path += '/' +web_url.split('/', 2)[2]
        urls = fetch_image_urls(web_url)
        if not len(urls[0])<=5:
            download_images(urls[0], folder_path)
            print(f"Downloaded {len(urls[0])} images to {folder_path}")
    
    print(f"Next Downloading images from {urls[1]}")
    main(urls[1])

if __name__ == "__main__":
    main('https://bakufu.jp/archives/1040235')