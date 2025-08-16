import os
import time
import random
import base64
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from urllib.parse import urljoin

firefox_options = Options()
firefox_options.add_argument("--headless")
# Torプロキシ設定（profileではなくオプションプリファレンスで一元化）
firefox_options.set_preference("network.proxy.type", 1)
firefox_options.set_preference("network.proxy.socks", "127.0.0.1")
firefox_options.set_preference("network.proxy.socks_port", 9050)
firefox_options.set_preference("network.proxy.socks_remote_dns", True)

# Selenium Managerに任せるためgeckodriverパスは明示しない

def collect_next_page(driver, current_url):
    """次ページ候補URLを収集しランダムで1件返す"""
    a_elements = driver.find_elements(By.TAG_NAME, 'a')
    next_page_url_array = []
    exclude_ext = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp', '.avif')
    for a in a_elements:
        href = a.get_attribute('href')
        if not href:
            continue
        lower = href.lower()
        if lower.endswith(exclude_ext):
            continue
        next_page_url_array.append(href)
    if next_page_url_array:
        # 同一URLを除外
        filtered = [u for u in next_page_url_array if u != current_url]
        if filtered:
            return random.choice(filtered)
    return ''

def save_rendered_images_without_extra_download(driver, folder_path, min_w=300, min_h=250):
    """全画像を要素スクリーンショット(PNG)で保存（追加HTTPダウンロード無し）。"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    count = 0
    img_elements = driver.find_elements(By.TAG_NAME, 'img')
    for idx, img in enumerate(img_elements):
        try:
            size = driver.execute_script(
                "return [arguments[0].naturalWidth, arguments[0].naturalHeight];", img
            )
            if not size or len(size) != 2:
                continue
            w, h = size
            if w < min_w or h < min_h:
                continue
            png_bytes = img.screenshot_as_png
            out_path = os.path.join(folder_path, f"img_{idx:03d}.png")
            with open(out_path, 'wb') as f:
                f.write(png_bytes)
            count += 1
            print(f"Saved screenshot => {out_path} ({w}x{h})")
        except Exception as e:
            print(f"Skip image idx={idx} error={e}")
            continue
    return count

def wait_initial_load(driver, timeout=5):
    """簡易待機: DOM安定を目安に短時間スリープ（高度な待機は未実装）"""
    time.sleep(timeout)

def main(start_url):
    driver = webdriver.Firefox(options=firefox_options)
    try:
        url = start_url
        page_index = 1
        while url:
            print(f"[Page {page_index}] Processing {url}")
            driver.get(url)
            wait_initial_load(driver, timeout=3)
            folder_path = './downloaded_images/' + url.split('/', 2)[2]
            saved = save_rendered_images_without_extra_download(driver, folder_path)
            print(f"Saved {saved} images to {folder_path}")
            next_url = collect_next_page(driver, url)
            if next_url and next_url != url:
                print(f"Next candidate: {next_url}")
                url = next_url
                page_index += 1
            else:
                print("No more pages to process or next URL invalid.")
                break
    finally:
        driver.quit()

if __name__ == "__main__":
    main('https://bakufu.jp/archives/category/av%e7%b4%a0%e4%ba%ba')