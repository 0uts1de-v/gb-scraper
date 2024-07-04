import os
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)


def scrape(tags, page=1, save_dir='downloads'):
    base_url = 'https://gelbooru.com'
    tag_query = '+'.join(tags)
    url = f'{base_url}/index.php?page=post&s=list&tags={tag_query}&pid={page * 42}'
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    for post in soup.find_all('article', class_='thumbnail-preview'):
        post_link = post.find('a')['href']
        post_url = urljoin(base_url, post_link)
        
        post_response = requests.get(post_url)
        post_soup = BeautifulSoup(post_response.content, 'html.parser')
        
        image_tag = post_soup.find('img', id='image')
        if image_tag is None:
            print(f"Image not found for post: {post_url}")
            continue
        
        original_image = image_tag['src']
        
        original_image = urljoin(base_url, original_image)
        
        parsed_url = urlparse(post_url)
        query_params = dict(qc.split('=') for qc in parsed_url.query.split('&') if '=' in qc)
        image_id = query_params.get('id', 'unknown')
        image_name = sanitize_filename(f"{tag_query}_{image_id}")
        
        image_ext = os.path.splitext(original_image)[-1]

        if image_ext not in ['.jpg', '.jpeg', '.png']:
            print(f"Skipping non-static image: {original_image}")
            continue
        
        try:
            image_response = requests.get(original_image)
            image_response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to download image {original_image}: {e}")
            continue
        
        image_path = os.path.join(save_dir, f"{image_name}{image_ext}")
        
        with open(image_path, 'wb') as f:
            f.write(image_response.content)

        print(f"Saved: {image_path}")

        tags_path = os.path.join(save_dir, f"{image_name}.txt")
        tags_list = [a.text for a in post_soup.find_all('li', class_=['tag-type-character', 'tag-type-copyright', 'tag-type-general', 'tag-type-metadata', 'tag-type-artist'])]
        tags_list = [" ".join(tag.split(" ")[1:-1]) for tag in tags_list]
            
        with open(tags_path, 'w') as f:
            f.write(', '.join(tags_list))
        
        print(f"Saved: {tags_path}")


def main():
    tags = input("Enter tags: ").strip().split()
    pages = int(input("Enter pages (1-?): ").strip().split()[0])
    save_dir = "downloads"

    for page in range(pages):
        scrape(tags=tags, page=page, save_dir=save_dir)
    
    print(f"Images and tags saved in {save_dir}")


if __name__ == "__main__":
    main()

