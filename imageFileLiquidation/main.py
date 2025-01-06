import os
from PIL import Image

def delete_small_images(folder_path, min_size=300):
    for root, dirs, files in os.walk(folder_path):
        for filename in files:
            file_path = os.path.join(root, filename)
            try:
                with Image.open(file_path) as img:
                    if img.width < min_size or img.height < min_size:
                        os.remove(file_path)
                        print(f"Deleted {file_path} (size: {img.width}x{img.height})")
            except Exception as e:
                print(f"Error processing {file_path}: {e}")

def main():
    folder_path = '/home/user/Documents/workspace/downloaded_images'
    delete_small_images(folder_path)

if __name__ == "__main__":
    main()