import os
import sys
import json
from bs4 import BeautifulSoup
from typing import List
from ollama import chat
from pydantic import BaseModel

# Define the structure of the question schema
class QuestionOption(BaseModel):
    text: str
    correct: bool

class Question(BaseModel):
    question: str
    options: List[QuestionOption]
    answer_explanation: str

class QuestionSchema(BaseModel):
    questions: List[Question]

question_schema = QuestionSchema.model_json_schema()

def generate_questions_from_content(content):
    """Generate multiple choice questions using Ollama's chat API."""
    prompt = (
        f"Create three different multiple-choice questions based on the following content. "
        f"Each question should have unique options and cover distinct aspects of the content and this is for a technical audience, don't make the wrong answers too obvious.\n\n"
        f"{content}"
    )

    # try:
    response = chat(
        model="llama3.2",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        format=question_schema,
    )
    print(response)
    response_content = response.message.content
    questions_data = json.loads(response_content).get("questions", [])
    return questions_data
    # except Exception as e:
    #     print(f"Error generating questions: {e}")
    #     return None

def format_question_to_markdown(question_data):
    """Format the question and answers into markdown format."""
    markdown = f"**Question:** {question_data['question']}\n\n"
    markdown += "**Options:**\n"
    for idx, option in enumerate(question_data['options'], 1):
        markdown += f"- {chr(64 + idx)}. {option['text']}\n"

    # Find the correct answer safely
    try:
        correct_idx = next(idx for idx, option in enumerate(question_data['options'], 1) if option['correct'])
        correct_label = chr(64 + correct_idx)
    except StopIteration:
        correct_label = "N/A"  # No correct answer provided

    markdown += f"\n**Correct Answer:** {correct_label}\n"
    markdown += f"\n**Explanation:** {question_data.get('answer_explanation', 'No explanation provided.')}\n"
    return markdown

def process_files(lesson_folder_path, questions_folder_path):
    """Process all files in the given folder and generate questions."""
    if not os.path.exists(questions_folder_path):
        os.makedirs(questions_folder_path)

    for filename in os.listdir(lesson_folder_path):
        if filename.endswith('.html'):
            lesson_path = os.path.join(lesson_folder_path, filename)

            with open(lesson_path, 'r', encoding='utf-8') as file:
                soup = BeautifulSoup(file, 'html.parser')

                # Extract the content of the lesson
                content = soup.get_text(strip=True)

                # Get the title of the lesson (assumes <h1> tag for title)
                h1_tag = soup.find('h1')
                lesson_title = h1_tag.get_text(strip=True) if h1_tag else filename

                print(f"Processing lesson: {lesson_title}")

                # Generate three distinct multiple choice questions based on the content
                questions = generate_questions_from_content(content)
                if questions:
                    # Create a markdown file for this lesson
                    markdown_filename = os.path.splitext(filename)[0] + '.md'
                    markdown_path = os.path.join(questions_folder_path, markdown_filename)

                    with open(markdown_path, 'w', encoding='utf-8') as md_file:
                        md_file.write(f"# Questions for: {lesson_title}\n\n")
                        for idx, question_data in enumerate(questions, 1):
                            md_file.write(f"## Question {idx}\n\n")
                            markdown_content = format_question_to_markdown(question_data)
                            md_file.write(markdown_content)

                     # Save the questions as a JSON file
                    json_filename = os.path.splitext(filename)[0] + '.json'
                    json_path = os.path.join(questions_folder_path, json_filename)

                    with open(json_path, 'w', encoding='utf-8') as json_file:
                        json.dump({"questions": questions}, json_file, indent=2)

                    print(f"Questions saved to {markdown_filename} and {json_filename}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python create-questions.py <lesson_folder_path>")
        sys.exit(1)

    lesson_folder_path = sys.argv[1]

    if not os.path.isdir(lesson_folder_path):
        print(f"Error: '{lesson_folder_path}' is not a valid directory.")
        sys.exit(1)

    # Define the questions directory
    questions_folder_path = os.path.join(os.path.dirname(lesson_folder_path), 'questions')

    process_files(lesson_folder_path, questions_folder_path)
    print("Question generation complete.")

if __name__ == "__main__":
    main()
