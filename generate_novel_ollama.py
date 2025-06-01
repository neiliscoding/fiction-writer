import os
import requests
import json
from ebooklib import epub

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

BIBLE_TXT_FILE = "narrative_bible.txt"
BIBLE_JSON_FILE = "narrative_bible.json"
NOVEL_OUTPUT_FILE = "novel.txt"
NOVEL_EPUB_FILE = "novel.epub"

PROMPT = '''You are helping write a dark fantasy novel set in a fictional analog of medieval Europe. The tone is grim, violent, and sexually explicit, similar to Game of Thrones. Magic exists but is rare and dangerous. Violence is bloody and intense. Sex and nudity are frequent and treated with narrative seriousness.

Please generate a Narrative Bible for the story that includes:

1. **Characters**: At least 6 major characters, including name, role, background, motivations, and relationships to others.

2. **Locations**: At least 5 detailed locations, such as cities, castles, or regions. Include political significance or historical notes.

3. **Themes & Tone**: Describe the narrative voice, primary themes (e.g., betrayal, ambition), and general tone of the novel.

4. **Plot Outline**: Create a 12-chapter outline that traces a primary arc (political, personal, or magical). Include major events, conflicts, and turning points.

Present the content in Markdown-like readable structure.
'''

def query_ollama(prompt):
    response = requests.post(OLLAMA_URL, json={
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    })
    response.raise_for_status()
    return response.json()["response"]

def save_outputs(markdown_text):
    with open(BIBLE_TXT_FILE, 'w', encoding='utf-8') as f:
        f.write(markdown_text)
    print(f"Saved human-readable Bible to {BIBLE_TXT_FILE}")

    sections = markdown_text.split("\n## ")
    bible = {}
    for section in sections:
        if section.strip():
            lines = section.strip().split("\n", 1)
            key = lines[0].strip().lower().replace(" ", "_")
            value = lines[1].strip() if len(lines) > 1 else ""
            bible[key] = value
    with open(BIBLE_JSON_FILE, 'w', encoding='utf-8') as f:
        json.dump(bible, f, indent=2)
    print(f"Saved structured Bible to {BIBLE_JSON_FILE}")

def export_to_epub(text):
    book = epub.EpubBook()
    book.set_identifier("novel-id")
    book.set_title("Dark Fantasy Novel")
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

def generate_full_novel():
    if not os.path.exists(BIBLE_TXT_FILE):
        print("Narrative Bible not found. Run the narrative bible generator first.")
        return

    with open(BIBLE_TXT_FILE, 'r', encoding='utf-8') as f:
        bible_text = f.read()

    full_prompt = f'''You are writing a complete dark fantasy novel based on the following Narrative Bible. The tone should remain consistent throughout: dark, violent, and sexually explicit. Magic is rare and mysterious. Fighting is graphic and brutal. Include explicit scenes where contextually appropriate.

Use the characters, locations, tone, and plot outline provided below.

---

{bible_text}

---

Write a full novel of approximately 20,000 words, divided into 12 chapters. Use clear chapter headings (e.g., ## Chapter 1: Title) and maintain a tight narrative focus.
'''

    print("Generating full novel. This may take a while...")
    response = query_ollama(full_prompt)

    with open(NOVEL_OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(response)
    print(f"Saved full novel to {NOVEL_OUTPUT_FILE}")

    export_to_epub(response)

def main():
    print("Generating narrative bible...")
    bible = query_ollama(PROMPT)
    save_outputs(bible)

    print("\n--- Proceeding to generate full novel ---\n")
    generate_full_novel()

if __name__ == "__main__":
    main()
