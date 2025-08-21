from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
from urllib.parse import urljoin
import random
import base64
import time

# Tor proxy設定
firefox_options = Options()
firefox_options.add_argument("--headless")
firefox_options.set_preference("network.proxy.type", 1)
firefox_options.set_preference("network.proxy.socks", "127.0.0.1")
firefox_options.set_preference("network.proxy.socks_port", 9050)
firefox_options.set_preference("network.proxy.socks_remote_dns", True)

# グローバルドライバ
driver = webdriver.Firefox(options=firefox_options)

def _generate_filename(img_url, idx, suffix=""):
    """画像URLからファイル名を生成する（内部ヘルパー）"""
    # base64 URLの場合
    if img_url.startswith('data:image/'):
        return f"data_img_{idx:03d}{suffix}.png"
    
    # 通常のURL処理
    filename = img_url.split('/')[-1].split('?')[0]
    if not filename.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
        filename = f"img_{idx:03d}{suffix}.png"
    else:
        name_part, ext = os.path.splitext(filename)
        filename = f"{name_part}{suffix}{ext}"
    return filename

def save_base64_image(base64_data, folder_path, filename):
    """base64データから画像を保存する共通メソッド"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    try:
        # data:image/プレフィックスをチェック
        if not base64_data.startswith('data:image/'):
            print(f"Skip: invalid base64 data format")
            return False
            
        # base64デコードして保存
        image_data = base64.b64decode(base64_data.split(',')[1])
        img_path = os.path.join(folder_path, filename)
        
        with open(img_path, 'wb') as img_file:
            img_file.write(image_data)
        print(f"Saved base64 image: {filename}")
        return True
        
    except Exception as e:
        print(f"Error saving base64 image {filename}: {e}")
        return False

def create_download_folder_path(url, base_path='./downloaded_images'):
    """URLからダウンロード用のフォルダパスを生成する"""
    try:
        # URLからドメイン部分を抽出
        domain = url.split('/', 3)[2] if len(url.split('/')) > 2 else 'unknown'
        # 不正な文字を除去（Windows/Linuxファイルシステム対応）
        safe_domain = domain.replace(':', '_').replace('?', '_').replace('*', '_')
        folder_path = os.path.join(base_path, safe_domain)
        return folder_path
    except Exception as e:
        print(f"Error creating folder path from {url}: {e}")
        return os.path.join(base_path, 'unknown')

def fetch_image_urls(current_url, folder_path, driver):
    """指定URLから画像URLを抽出・フィルタリングする"""
    img_elements = driver.find_elements(By.TAG_NAME, 'img')
    img_urls = []
    base64_count = 0  # base64画像用の専用カウンタ
    
    for img_element in img_elements:
        try:
            # src属性の取得
            img_src = img_element.get_attribute('src')
            if not img_src:
                continue
                
            img_url = urljoin(current_url, img_src)
            print(f"check_img_url: {img_url}")
            
            if img_url.startswith('data:image/'):
                # base64画像は直接保存（専用カウンタを使用）
                filename = _generate_filename(img_url, base64_count, "_base")
                save_base64_image(img_url, folder_path, filename)
                base64_count += 1  # カウンタを増加
                continue
                
            # JavaScriptで画像サイズチェック
            size = driver.execute_script(
                "return [arguments[0].naturalWidth, arguments[0].naturalHeight];", img_element
            )
            if not size or len(size) != 2:
                continue
            w, h = size
            
            if w >= 300 and h >= 250:
                img_urls.append((img_url, img_element))  # 要素も一緒に保持
                print(f"img_url: {img_url}")
                
        except Exception as e:
            print(f"Error processing image: {e}")
            continue
    
    print(f"img_urls: {len(img_urls)} images found")
    return img_urls

def find_next_page_url(current_url, driver):
    """次ページのURL候補を取得してランダムに1つ選択する"""
    link_elements = driver.find_elements(By.TAG_NAME, 'a')
    next_page_url_array = []
    excluded_extensions = ('.jpg', '.gif', '.png', '.jpeg', '.webp', '.svg')
    
    for link_element in link_elements:
        try:
            href = link_element.get_attribute('href')
            if not href:
                continue
                
            next_page_url = urljoin(current_url, href)
            
            # 画像ファイル直リンクを除外
            if next_page_url.lower().endswith(excluded_extensions):
                continue
                
            # 同一URLを除外
            if next_page_url == current_url:
                continue
                
            next_page_url_array.append(next_page_url)
            
        except Exception as e:
            print(f"Error processing link: {e}")
            continue
    
    print(f"next_page_url_array: {len(next_page_url_array)} candidates found")
    
    if next_page_url_array:
        selected_url = next_page_url_array[random.randint(0, len(next_page_url_array) - 1)]
        print(f"next_url: {selected_url}")
        return selected_url
    else:
        print("No next page found")
        return ''

def download_images(img_data_list, folder_path, driver):
    """画像リストをCanvas+Base64方式でダウンロード・保存する"""
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    for idx, (img_url, img_element) in enumerate(img_data_list):
        try:
            # JavaScriptでCanvas+Base64取得（右クリック保存と同等）
            script = """
            return new Promise((resolve) => {
                var img = arguments[0];
                var canvas = document.createElement('canvas');
                var ctx = canvas.getContext('2d');
                canvas.width = img.naturalWidth;
                canvas.height = img.naturalHeight;
                ctx.drawImage(img, 0, 0);
                canvas.toBlob((blob) => {
                    var reader = new FileReader();
                    reader.onload = () => resolve(reader.result);
                    reader.readAsDataURL(blob);
                }, 'image/png');
            });
            """
            
            base64_data = driver.execute_async_script(script, img_element)
            if not base64_data or not base64_data.startswith('data:image/'):
                print(f"Skip: invalid base64 data for {img_url}")
                continue
                
            # 共通の保存メソッドを使用
            filename = _generate_filename(img_url, idx, "_canvas")
            if save_base64_image(base64_data, folder_path, filename):
                print(f"Downloaded {img_url}")
            
        except Exception as e:
            print(f"Error downloading {img_url}: {e}")
            continue

def main(target_url):
    """メインループ - 再帰ではなくイテレーション処理"""
    current_url = target_url
    page_count = 0
    max_pages = 100  # 無限ループ防止
    
    print(f"Starting scraper from: {target_url}")
    
    while current_url and page_count < max_pages:
        page_count += 1
        print(f"\n--- Page {page_count} ---")
        print(f"Downloading images from {current_url}")
        
        try:
            # ページ取得と動的読み込み完了待機
            driver.get(current_url)
            
            # DOM要素の準備完了を待機（最大10秒、通常はもっと早く完了）
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
            
            # フォルダパス作成を専用メソッドに委譲
            folder_path = create_download_folder_path(current_url)
            
            # 画像取得（各メソッド内で要素取得を行う）
            img_urls = fetch_image_urls(current_url, folder_path, driver)
            if len(img_urls) > 2:
                download_images(img_urls, folder_path, driver)
            print(f"Downloaded {len(img_urls)} images to {folder_path}")
            
            # 次ページURL決定（各メソッド内で要素取得を行う）
            current_url = find_next_page_url(current_url, driver)
            
        except Exception as e:
            print(f"Error processing {current_url}: {e}")
            break
    
    print("No more pages to process")
    if page_count >= max_pages:
        print(f"Reached maximum page limit: {max_pages}")
    
    print(f"Scraping completed. Processed {page_count} pages.")

if __name__ == "__main__":
    try:
        main('https://bakufu.jp/archives/category/av%e7%b4%a0%e4%ba%ba')
    finally:
        driver.quit()