import os
import sys
import csv
import subprocess
from bs4 import BeautifulSoup

def to_title_case_with_ollama_cli(text):
    """Use Ollama CLI with Mistral model to convert text to title case."""
    prompt = f"Convert the following text to title case while maintaining context:\n\n{text}\n\nReturn only the corrected title in title case."
    try:
        result = subprocess.run(
            ["ollama", "run", "mistral", prompt],
            capture_output=True,
            text=True,
            check=True
        )
        corrected_title = result.stdout.strip()
        if not corrected_title:
            print(f"Error: Empty response for title '{text}'")
            corrected_title = text.title()  # Fallback to basic title case
        return corrected_title
    except subprocess.CalledProcessError as e:
        print(f"Error calling Ollama CLI: {e}")
        return text.title()  # Fallback in case of error

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
                    lesson_name = os.path.splitext(filename)[0]
                    writer.writerow({'Lesson Name': lesson_name, 'Original Title': '', 'Corrected Title': ''})

                    for heading in range(1, 8):
                        for tag in soup.find_all(f'h{heading}'):
                            original_title = tag.get_text(strip=True)
                            corrected_title = to_title_case_with_ollama_cli(original_title)

                            if original_title != corrected_title:
                                writer.writerow({
                                    'Lesson Name': '',
                                    'Original Title': original_title,
                                    'Corrected Title': corrected_title
                                })

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_titles_with_subprocess.py <folder_path>")
        sys.exit(1)

    folder_path = sys.argv[1]
    
    if not os.path.isdir(folder_path):
        print(f"Error: '{folder_path}' is not a valid directory.")
        sys.exit(1)

    process_files(folder_path)
    print("Title processing complete. Results saved in 'titles.csv'.")

if __name__ == "__main__":
    main()
