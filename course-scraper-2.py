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
    module_div.decompose()
    
    # Get the main content
    main_content_div = soup.find('div', class_='sensei-course-theme__main-content')
    main_content = main_content_div.encode_contents().decode('utf-8') if main_content_div else "<p>No content found</p>"
    
    return page_title, module_name, main_content

def save_module_html(module_number, module_name, lessons_content, output_folder):
    """Save the module content into an HTML file."""
    combined_html = '<html><head><title>' + module_name + '</title></head><body>'
    combined_html += f'<h1>{module_name}</h1>'
    
    for lesson_title, content in lessons_content:
        #combined_html += f'<h2>{lesson_title}</h2>'
        soup = BeautifulSoup(content, 'html.parser')
        
        # Increment the header levels
        for heading in soup.find_all(['h1','h2', 'h3', 'h4', 'h5', 'h6']):
            heading.name = f'h{int(heading.name[1]) + 1}'  # Increment header level by 1
            heading.attrs = {}  # Remove all attributes

        combined_html += str(soup)
    
    combined_html += '</body></html>'
    
    # Save the HTML file with numbering
    filename = os.path.join(output_folder, f"{module_number:02d}_{sanitize_filename(module_name)}.html")
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(combined_html)
    
    logging.info(f"Module saved to {filename}")

def process_lessons(session, links, cookie_header):
    """Process and group lessons by module."""
    modules = {}
    
    for link in links:
        lesson_title, module_name, content = download_and_process_content(session, link, cookie_header)
        
        if module_name not in modules:
            modules[module_name] = []
        
        modules[module_name].append((lesson_title, content))
    
    return modules

def combine_all_modules(modules, output_folder):
    """Combine all modules into a single HTML file."""
    combined_html = '<html><head><title>All Modules</title></head><body>'
    combined_html += '<h1>All Modules</h1>'
    
    for module_number, (module_name, lessons_content) in enumerate(modules.items(), start=1):
        combined_html += f'<h1>{module_number:02d}. {module_name}</h1>'
        
        for lesson_title, content in lessons_content:
            #combined_html += f'<h2>{lesson_title}</h2>'
            soup = BeautifulSoup(content, 'html.parser')
            
            # Increment the header levels
            for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
                heading.name = f'h{int(heading.name[1]) + 1}'  # Increment header level by 1
                heading.attrs = {}  # Remove all attributes
            
            combined_html += str(soup)
    
    combined_html += '</body></html>'
    
    # Save the combined HTML file
    filename = os.path.join(output_folder, "all_modules.html")
    with open(filename, 'w', encoding='utf-8') as file:
        file.write(combined_html)
    
    logging.info(f"All modules combined into {filename}")

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
    
    # Create a folder for saving output
    response = session.get(url, headers={'Cookie': cookie_header})
    log_request_and_response(response)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    folder_title = "output-" + sanitize_filename(soup.find('title').get_text(strip=True))
    os.makedirs(folder_title, exist_ok=True)
    
    # Process lessons and group them by module
    modules = process_lessons(session, links, cookie_header)
    
    # Save each module's content in a separate file
    for module_number, (module_name, lessons_content) in enumerate(modules.items(), start=1):
        save_module_html(module_number, module_name, lessons_content, folder_title)
    
    # Combine all modules into a single file
    combine_all_modules(modules, folder_title)
    
    logging.info("Content download, processing, and saving complete.")

if __name__ == "__main__":
    main()
