import requests
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import random
from PIL import Image, UnidentifiedImageError
from io import BytesIO

# Configure requests to use Tor
proxies = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

def fetch_image_urls(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    response = requests.get(url, headers=headers, proxies=proxies)
    soup = BeautifulSoup(response.text, 'html.parser')
    img_tags = soup.find_all('img')
    img_urls = []
    next_url = ''
    site_403 = False
    
    for img in img_tags:
        if 'src' in img.attrs :
            img_url = urljoin(url, img['src'])
            print(f"check_img_url: {img_url}")
            if img_url.startswith('data:image/'):
                print("Skipping base64 image")
                continue
            img_response = requests.get(img_url, headers=headers, proxies=proxies)
            print(f"img_response: {img_response}")
            if img_response.status_code == 200:# and 'image' in img_response.headers['Content-Type']:
                try:
                    img_obj = Image.open(BytesIO(img_response.content))
                    if img_obj.width >= 300 and img_obj.height >= 250:
                        img_urls.append(img_url)
                        print(f"img_url: {img_url}")
                except UnidentifiedImageError:
                    print(f"Cannot identify image file: {img_url}")
            elif img_response.status_code == 403:
                #print("image is 403 Forbidden")
                #continue
                print("Site is 403 Forbidden")
                site_403 = True
        if site_403:
            break
    
    print(f"img_urls: {img_urls}")
    
    # Find the next page URL
    next_page_tags = soup.find_all('a')
    next_page_url_array = []
    for next_page_tag in next_page_tags:
        if 'href' in next_page_tag.attrs:
            next_page_url = urljoin(url, next_page_tag['href'])
            if not next_page_url.endswith('.jpg') and not next_page_url.endswith('.gif') :#and not next_page_url.startswith('http:'):
                next_page_url_array.append(next_page_url)
    print(f"next_page_url_array: {next_page_url_array}")
    if next_page_url_array:
        next_url = next_page_url_array[random.randint(0, len(next_page_url_array) - 1)]
        print(f"next_url: {next_url}")
    else:
        next_url = ''
        print("No next page found")
    return img_urls,next_url

def download_images(img_urls, folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    for img_url in img_urls:
        img_name = os.path.join(folder_path, img_url.split('/')[-1])
        with open(img_name, 'wb') as img_file:
            img_file.write(requests.get(img_url, proxies=proxies).content)
            print(f"Downloaded {img_url}")

def main(target_url):
    if len(target_url) != 0:
        print(f"Downloading images from {target_url}")
        web_url = target_url  # Replace with the target URL
        folder_path = './downloaded_images'
        folder_path += '/' +web_url.split('/', 2)[2]
        urls = fetch_image_urls(web_url)
        if not len(urls[0])<=2:
            download_images(urls[0], folder_path)
        print(f"Downloaded {len(urls[0])} images to {folder_path}")
    
    if urls[1]:  # Check if next_url exists
        print(f"Next Downloading images from {urls[1]}")
        main(urls[1])
    else:
        print("No more pages to process")

if __name__ == "__main__":
    main('https://bakufu.jp/archives/category/av%e7%b4%a0%e4%ba%ba')