import os
import sys
import csv
from bs4 import BeautifulSoup
from titlecase import titlecase

def extract_content_from_html(html_content):
    """Extract content from <p>, <li>, and header tags using BeautifulSoup."""
    soup = BeautifulSoup(html_content, 'html.parser')
    content_parts = []
    headers = []

    # Extract text from <p> and <li> tags
    for tag in soup.find_all(['p', 'li']):
        content_parts.append(tag.get_text(strip=True))

    # Extract headers (h1 to h6)
    for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        headers.append(header.get_text(strip=True))

    return "\n".join(content_parts), headers

def find_sentences_missing_punctuation(content):
    """Identify sentences in the content that do not end with . : ? or !."""
    issues = []
    sentences = content.split('\n')
    for sentence in sentences:
        stripped_sentence = sentence.strip()
        if stripped_sentence and not stripped_sentence.endswith(('.', ':', '?', '!','”')):
            issues.append(stripped_sentence)
    return issues

def find_non_title_case_headers(headers):
    """Identify headers that are not in title case."""
    issues = []
    for header in headers:
        title_case_header = titlecase(header, callback=case_exceptions)
        if header != titlecase(header):
            issues.append(header + " -> " + titlecase(header))
    return issues

def case_exceptions(word, **kwargs):
   if word.upper() in ('TCP', 'UDP', 'VS'):
     return word.upper()

def process_files(lesson_folder_path, output_csv_path):
    """Process all files in the given folder and find sentences and headers with issues."""
    grammar_issues = []

    for filename in os.listdir(lesson_folder_path):
        if filename.endswith('.html'):
            lesson_path = os.path.join(lesson_folder_path, filename)

            with open(lesson_path, 'r', encoding='utf-8') as file:
                html_content = file.read()

                # Extract content and headers directly from HTML
                content, headers = extract_content_from_html(html_content)

                # Find sentences missing punctuation
                sentence_issues = find_sentences_missing_punctuation(content)

                # Find headers not in title case
                header_issues = find_non_title_case_headers(headers)

                for issue in sentence_issues:
                    grammar_issues.append({"filename": filename, "issue": issue, "type": "Sentence Punctuation"})

                for issue in header_issues:
                    grammar_issues.append({"filename": filename, "issue": issue, "type": "Header Case"})

    # Write all grammar issues to a CSV file
    with open(output_csv_path, 'w', encoding='utf-8', newline='') as csvfile:
        fieldnames = ["filename", "issue", "type"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(grammar_issues)

    print(f"Issues saved to {output_csv_path}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python check-punctuation.py <lesson_folder_path>")
        sys.exit(1)

    lesson_folder_path = sys.argv[1]

    if not os.path.isdir(lesson_folder_path):
        print(f"Error: '{lesson_folder_path}' is not a valid directory.")
        sys.exit(1)

    # Define the output CSV file
    output_csv_path = os.path.join(os.path.dirname(lesson_folder_path), 'punctuation_issues.csv')

    process_files(lesson_folder_path, output_csv_path)
    print("Punctuation and header case check complete.")

if __name__ == "__main__":
    main()
