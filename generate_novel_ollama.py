import os
import requests
import json
import re
from ebooklib import epub

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

CHARACTERS_FILE = "characters.json"
LOCATION_FILE = "location.json"
OUTLINE_FILE = "story_outline.json"
NOVEL_OUTPUT_FILE = "novel.txt"
NOVEL_HTML_FILE = "novel.html"
NOVEL_EPUB_FILE = "novel.epub"

def query_ollama(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    })
    response.raise_for_status()
    return response.json()["response"]

def extract_json(text):
    match = re.search(r'(\{.*\}|\[.*\])', text, re.DOTALL)
    if not match:
        raise ValueError("No valid JSON object found in response.")
    return json.loads(match.group(0))

def generate_characters():
    prompt = '''Create a JSON object with one main character and two sub-characters. For each character, include:
- name
- role (main or sub)
- background
- personality
- goal
- relationship to the others
Return only valid JSON.'''
    print("Generating characters...")
    characters_json_str = query_ollama(prompt).strip()
    print("Characters Generated:")
    print(characters_json_str)
    characters_data = extract_json(characters_json_str)
    with open(CHARACTERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(characters_data, f, indent=2)
    print(f"Saved characters to {CHARACTERS_FILE}")

def generate_location():
    prompt = '''Create a JSON object describing one fantasy location. Include:
- name
- type (city, forest, castle, etc.)
- physical description
- cultural or political significance
Return only valid JSON.'''
    print("Generating location...")
    location_json_str = query_ollama(prompt).strip()
    print("Location Generated:")
    print(location_json_str)
    location_data = extract_json(location_json_str)
    with open(LOCATION_FILE, 'w', encoding='utf-8') as f:
        json.dump(location_data, f, indent=2)
    print(f"Saved location to {LOCATION_FILE}")

def generate_outline():
    with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
        characters = f.read()
    with open(LOCATION_FILE, 'r', encoding='utf-8') as f:
        location = f.read()

    prompt = f'''Using the following characters and location, create a story outline with three chapters: beginning, middle, and end. Each chapter should include a title and a short summary.

Characters:
{characters}

Location:
{location}

Return only valid JSON with this structure:
[
  {{"chapter": 1, "title": "...", "summary": "..."}},
  {{"chapter": 2, "title": "...", "summary": "..."}},
  {{"chapter": 3, "title": "...", "summary": "..."}}
]'''

    print("Generating outline...")
    outline_json_str = query_ollama(prompt).strip()
    print("Outline Generated:")
    print(outline_json_str)
    outline_data = extract_json(outline_json_str)
    with open(OUTLINE_FILE, 'w', encoding='utf-8') as f:
        json.dump(outline_data, f, indent=2)
    print(f"Saved outline to {OUTLINE_FILE}")

def generate_chapters():
    with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
        characters = json.load(f)
    with open(LOCATION_FILE, 'r', encoding='utf-8') as f:
        location = json.load(f)
    with open(OUTLINE_FILE, 'r', encoding='utf-8') as f:
        outline = json.load(f)

    full_novel = ""
    html_content = """<html><head>
    <meta charset='UTF-8'>
    <title>Short Fantasy Story</title>
    <link href='https://cdn.jsdelivr.net/npm/barecss@1.1.1/css/bare.min.css' rel='stylesheet'>
</head><body><div class='container'>"""

    for chapter in outline:
        chapter_number = chapter["chapter"]
        title = chapter["title"]
        summary = chapter["summary"]

        prompt = f'''Write Chapter {chapter_number} of a fantasy story.

Title: {title}
Summary: {summary}

Characters:
{json.dumps(characters, indent=2)}

Location:
{json.dumps(location, indent=2)}

Use all of the above characters and the location in this chapter.

Write the story scene for this chapter in full prose, 1000–1500 words. Use a dark, detailed tone. Begin with "## Chapter {chapter_number}: {title}".'''

        print(f"\n--- Generating Chapter {chapter_number}: {title} ---")
        chapter_text = query_ollama(prompt)
        print(f"Chapter {chapter_number} Text:\n{chapter_text}\n")

        full_novel += chapter_text.strip() + "\n\n"
        html_content += f'<h2>Chapter {chapter_number}: {title}</h2><p>{chapter_text.strip().replace("\n", "<br>")}</p>'

    html_content += "</div></body></html>"

    illustration_prompt = f"""Create a prompt for a fantasy book cover illustration. The tone is dark and moody. Use the following characters and location:\nCharacters:\n{json.dumps(characters, indent=2)}\n\nLocation:\n{json.dumps(location, indent=2)}\n\nMake the prompt suitable for use in an AI image generation tool."""
    illustration_description = query_ollama(illustration_prompt).strip()
    full_novel += f"\n\n[Illustration Prompt]\n{illustration_description}\n"

    with open(NOVEL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_novel)
    print(f"Saved full novel to {NOVEL_OUTPUT_FILE}")

    with open(NOVEL_HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Saved HTML to {NOVEL_HTML_FILE}")

    export_to_epub(full_novel)

def export_to_epub(text):
    book = epub.EpubBook()
    book.set_identifier("novel-id")
    book.set_title("Short Fantasy Story")
    book.set_language("en")
    book.add_author("AI Generated")

    chapter_list = text.split("## Chapter ")
    chapters = []

    for i, content in enumerate(chapter_list):
        if not content.strip():
            continue
        lines = content.split("\n", 1)
        title = f"Chapter {lines[0].strip()}"
        body = lines[1].strip() if len(lines) > 1 else ""
        c = epub.EpubHtml(title=title, file_name=f'chap_{i+1}.xhtml', lang='en')
        c.content = f'<h2>{title}</h2><p>{body.replace("\n", "<br>")}</p>'
        book.add_item(c)
        chapters.append(c)

    book.toc = chapters
    book.spine = ['nav'] + chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(NOVEL_EPUB_FILE, book, {})
    print(f"Saved EPUB to {NOVEL_EPUB_FILE}")

def main():
    generate_characters()
    generate_location()
    generate_outline()
    generate_chapters()

if __name__ == "__main__":
    main()
