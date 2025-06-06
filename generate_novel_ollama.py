import os
import requests
import json
import re
from ebooklib import epub
from diffusers import StableDiffusionPipeline
import torch

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
    global book_title

    with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
        characters = f.read()
    with open(LOCATION_FILE, 'r', encoding='utf-8') as f:
        location = f.read()

    prompt = f'''Using the following characters and location, create a story outline with three chapters: beginning, middle, and end. Each chapter should include a title and a short summary. Also generate a strong, compelling book title for the story.

Characters:
{characters}

Location:
{location}

Return only valid JSON with two parts:
{{
  "title": "...",
  "outline": [
    {{"chapter": 1, "title": "...", "summary": "..."}},
    {{"chapter": 2, "title": "...", "summary": "..."}},
    {{"chapter": 3, "title": "...", "summary": "..."}}
  ]
}}'''

    print("Generating outline...")
    outline_json_str = query_ollama(prompt).strip()
    print("Outline Generated:")
    print(outline_json_str)
    outline_data = extract_json(outline_json_str)
    book_title = outline_data["title"]
    outline = outline_data["outline"]
    with open(OUTLINE_FILE, 'w', encoding='utf-8') as f:
        json.dump(outline_data, f, indent=2)
    print(f"Saved outline to {OUTLINE_FILE}")

def generate_chapters():
    with open(CHARACTERS_FILE, 'r', encoding='utf-8') as f:
        characters = json.load(f)
    with open(LOCATION_FILE, 'r', encoding='utf-8') as f:
        location = json.load(f)
    with open(OUTLINE_FILE, 'r', encoding='utf-8') as f:
        outline_data = json.load(f)

    outline = outline_data["outline"]
    global book_title
    book_title = outline_data["title"]

    full_novel = f"{book_title}\n\n"
    html_content = f"""<html><head>
    <meta charset='UTF-8'>
    <title>{book_title}</title>
    <link href='https://cdn.jsdelivr.net/npm/barecss@1.1.1/css/bare.min.css' rel='stylesheet'>
</head><body><div class='container'>
<h1>{book_title}</h1>
<img src='cover.png' alt='Book Cover' width='320' height='432' style='display:block;margin:1em auto;'>"""

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

Write the story scene for this chapter in full prose, 2500–3000 words. Use a dark, detailed tone. Begin with "## Chapter {chapter_number}: {title}".'''

        print(f"\n--- Generating Chapter {chapter_number}: {title} ---")
        chapter_text = query_ollama(prompt)
        print(f"Chapter {chapter_number} Text:\n{chapter_text}\n")

        full_novel += chapter_text.strip() + "\n\n"
        html_content += f'<h2>Chapter {chapter_number}: {title}</h2><p>{chapter_text.strip().replace("\n", "<br>")}</p>'

    html_content += "</div></body></html>"

    illustration_prompt = f"""Create a prompt for a fantasy book cover illustration. The tone is dark and moody. Use the following characters and location:
Characters:
{json.dumps(characters, indent=2)}

Location:
{json.dumps(location, indent=2)}

Make the prompt suitable for use in an AI image generation tool. The final prompt must not exceed 75 words total."""
    illustration_description = query_ollama(illustration_prompt).strip()
    if len(illustration_description.split()) > 75:
        illustration_description = ' '.join(illustration_description.split()[:75])
    full_novel += f"\n\n[Illustration Prompt]\n{illustration_description}\n"

    print("Generating cover image with Stable Diffusion XL...")
    pipe = StableDiffusionPipeline.from_pretrained(
        "D:/models/models--runwayml--stable-diffusion-v1-5/snapshots/451f4fe16113bff5a5d2269ed5ad43b0592e9a14")
    pipe = pipe.to("cpu")  # Removed float16 for CPU compatibility

    image = pipe(illustration_description, height=432, width=320, num_inference_steps=20).images[0]
    image.save("cover.png")
    print("Saved cover image to cover.png")

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
    book.set_title(book_title)
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

    # Embed the cover image
    if os.path.exists("cover.png"):
        with open("cover.png", "rb") as img_file:
            cover_item = epub.EpubItem(uid="cover", file_name="images/cover.png", media_type="image/png", content=img_file.read())
            book.add_item(cover_item)
            book.set_cover("cover.png", img_file.read())
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
