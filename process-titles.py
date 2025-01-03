import os
import sys
import csv
import string
import re
from bs4 import BeautifulSoup

# Lowercase exceptions: words that should be in lowercase unless they're the first/last word
LOWERCASE_EXCEPTIONS = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "if", "in", "nor", "of", "on", "or", "so", "the", 
    "to", "up", "yet", "with", "within", "about", "after", "against", "along", "among", "around", "before", 
    "between", "during", "except", "following", "in", "into", "near", "next", "over", "through", "throughout", 
    "under", "until", "upon", "via", "with", "without", "toward", "towards", "despite", "because", "although",
    "during", "except", "inside", "outside", "underneath", "besides", "beyond", "toward", "whilst", "until", 
    "whether", "by", "how", "so", "such", "that", "which", "who", "whom", "whose", "where", "when", "vs", "are"
}

# Uppercase exceptions: words that should always be in uppercase
UPPERCASE_EXCEPTIONS = {
    "php", "wp", "wp-cli", "ssh", "vvv", "http", "https", "ide", "explain", "api", "rest", "apm", "oom", "wsod", "bom", "cli", "gui", "ajax"
}

# Trademark exceptions: words that should always appear exactly as specified (case-sensitive)
TRADEMARK_EXCEPTIONS = {
    "WordPress", "WordPress.com", "MySQL", "SQLite", "PHPStan", "PHPMD", "VIP", "JavaScript", "PHPCS", "PHPMyAdmin", "HeidiSQL", "TablePlus", "wp-env", "JS", "DevTools", "XDebug", "VSCode", "WebDriver"
}

def to_title_case(text):
    """Convert text to title case, handling lowercase, uppercase, and trademark exceptions."""
    
    # Step 1: Split the original text into words
    words = text.split()

    # Step 2: Initialize a list to store the final title-cased words
    title_cased_words = []

    # Step 3: Iterate through the original words and apply necessary transformations
    for i, word in enumerate(words):
        # If the word is a trademark exception, preserve the original case
        if word in TRADEMARK_EXCEPTIONS:
            title_cased_words.append(word)  # Keep trademark exceptions as is
        else:
            # Apply title case to other words
            title_cased_word = word.title()

            # Lowercase exceptions (unless they're the first or last word)
            if title_cased_word.lower() in LOWERCASE_EXCEPTIONS and i != 0 and i != len(words) - 1:
                title_cased_words.append(title_cased_word.lower())
            else:
                # Uppercase exceptions (e.g., PHP, WP, etc.)
                if title_cased_word.lower() in UPPERCASE_EXCEPTIONS:
                    title_cased_words.append(title_cased_word.upper())
                else:
                    # Default: Add the title-cased word
                    title_cased_words.append(title_cased_word)

    # Join the processed words back into a single string
    return " ".join(title_cased_words)




def process_files(folder_path):
    """Process all files in the given folder."""
    with open('titles.csv', mode='w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Lesson Name', 'Original Title', 'Corrected Title']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for filename in os.listdir(folder_path):
            if filename.endswith('.html'):
                lesson_path = os.path.join(folder_path, filename)
                
                with open(lesson_path, 'r', encoding='utf-8') as file:
                    soup = BeautifulSoup(file, 'html.parser')
                     # Get the title of the page from the <h1> tag
                    h1_tag = soup.find('h1')
                    page_title = h1_tag.get_text(strip=True) if h1_tag else 'No Title'

                    lesson_name = h1_tag.get_text(strip=True) if h1_tag else 'No Title'
                    writer.writerow({'Lesson Name': lesson_name, 'Original Title': '', 'Corrected Title': ''})

                    for heading in range(1, 8):
                        for tag in soup.find_all(f'h{heading}'):

                            # Skip module heading
                            if heading == 3 and 'wp-block-sensei-lms-course-theme-lesson-module' in tag.get('class', []):
                                continue

                            original_title = tag.get_text(strip=True)
                            corrected_title = to_title_case(original_title)

                            if original_title != corrected_title:
                                writer.writerow({
                                    'Lesson Name': '',
                                    'Original Title': original_title,
                                    'Corrected Title': corrected_title
                                })

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_titles.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        sys.exit(1)

    process_files(folder_path)
    print("Title processing complete. Results saved in 'titles.csv'.")

if __name__ == "__main__":
    main()
