import os
import sys
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import logging

# Setup logging for verbose HTTP output
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def get_cookie_header():
    """Read the entire Cookie header from cookies.txt as a single string."""
    try:
        with open('cookies.txt', 'r') as file:
            cookie_header = file.read().strip()
            if not cookie_header:
                raise ValueError("Cookie header is empty.")
            return cookie_header
    except FileNotFoundError:
        logging.error("Error: 'cookies.txt' file not found.")
        sys.exit(1)
    except ValueError as e:
        logging.error(str(e))
        sys.exit(1)

def get_session_with_proxy():
    """Create a session using a SOCKS5 proxy."""
    session = requests.Session()
    session.proxies = {
        'http': 'socks5://localhost:8080',
        'https': 'socks5://localhost:8080'
    }
    return session

def log_request_and_response(response):
    """Log detailed request and response information."""
    request = response.request
    logging.debug(f"REQUEST URL: {request.url}")
    logging.debug(f"REQUEST HEADERS:\n{request.headers}")
    logging.debug(f"RESPONSE STATUS: {response.status_code}")
    logging.debug(f"RESPONSE HEADERS:\n{response.headers}")

def get_links_with_class(session, url, class_name, cookie_header):
    headers = {'Cookie': cookie_header}
    response = session.get(url, headers=headers)
    log_request_and_response(response)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', class_=class_name)
    return [urljoin(url, link['href']) for link in links if 'href' in link.attrs]

def sanitize_filename(name):
    name = name.lower()
    name = re.sub(r'\s+', '-', name)
    name = re.sub(r'[^a-z0-9\-]', '', name)
    return name

def download_and_process_content(session, url, cookie_header):
    headers = {'Cookie': cookie_header}
    response = session.get(url, headers=headers)
    log_request_and_response(response)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    
      # List of classes to remove
    classes_to_remove = [
        'wp-block-sensei-lms-lesson-actions',
        'wp-block-sensei-lms-course-theme-prev-next-lesson',
        'sensei-course-theme-lesson-actions', 
        'sensei-course-theme-lesson-actions__complete-lesson-form',
        'wp-block-group sensei-lesson-footer'
    ]
    
    # Remove elements with the specified classes
    for class_name in classes_to_remove:
        for element in soup.find_all(class_=class_name):
            element.decompose()  
    
    # Get the page title
    page_title = soup.find('h1', class_='wp-block-post-title').get_text(strip=True)
    
    # Get the module name
    module_div = soup.find('h3', class_='wp-block-sensei-lms-course-theme-lesson-module')
    module_name = module_div.get_text(strip=True) if module_div else "unknown-module"
    
    # Get the main content
    main_content_div = soup.find('div', class_='sensei-course-theme__main-content')
    main_content = main_content_div.encode_contents().decode('utf-8') if main_content_div else "<p>No content found</p>"
    
    # Generate the filename
    prefix = sanitize_filename(module_name)
    lesson_name = sanitize_filename(page_title)
    filename = f"{prefix}-{lesson_name}.html"
    
    return filename, page_title, f"<html><head><title>{page_title}</title></head><body>{main_content}</body></html>"


def main():
    if len(sys.argv) != 2:
        logging.error("Usage: python script.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    class_name = 'wp-block-sensei-lms-course-outline-lesson'
    cookie_header = get_cookie_header()
    session = get_session_with_proxy()
    
    logging.info(f"Fetching links from {url}...")
    links = get_links_with_class(session, url, class_name, cookie_header)
    if not links:
        logging.warning("No links found with the specified class.")
        sys.exit(0)
    
    # Create a folder named after the page title
    response = session.get(url, headers={'Cookie': cookie_header})
    log_request_and_response(response)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    folder_title = "output-" + sanitize_filename(soup.find('title').get_text(strip=True))
    os.makedirs(folder_title, exist_ok=True)
    
    for link in links:
        filename, page_title, content = download_and_process_content(session, link, cookie_header)
        output_path = os.path.join(folder_title, filename)
        
        logging.info(f"Saving content from {link} to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(content)
    
    logging.info("Content download and processing complete.")

if __name__ == "__main__":
    main()
