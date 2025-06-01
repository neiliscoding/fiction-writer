import requests
import os
import time
from tqdm import tqdm
from datetime import datetime
import uuid
from ebooklib import epub

# --- CONFIGURATION ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"
BOOK_COUNT = 3
CHAPTER_COUNT = 12
CHAPTER_WORDS = 1000
IMAGE_PROMPT_WORDS = 200
OUTPUT_DIR = "chapters"
CHARACTER_DIR = "characters"
LOCATION_DIR = "locations"
SUMMARY_FILE = "full_story.txt"
EPUB_FILE = "full_story.epub"
DELAY_BETWEEN_CHAPTERS = 5

# --- SETUP ---
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CHARACTER_DIR, exist_ok=True)
os.makedirs(LOCATION_DIR, exist_ok=True)

# --- Placeholder for tracking character deaths ---
character_deaths = set()

# --- Utilities ---
def call_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "prompt": prompt,
            "stream": False
        }
    )
    response.raise_for_status()
    return response.json()["response"]

def save_entity(entity_text, label):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = uuid.uuid4().hex[:6]
    tag = "military_base" if "military" in entity_text.lower() else "alien_species" if "alien" in entity_text.lower() else "general"
    directory = CHARACTER_DIR if label.startswith("Character") else LOCATION_DIR
    filename = os.path.join(directory, f"{label.replace(' ', '_').lower()}_{tag}_{timestamp}_{unique_id}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(entity_text)
    print(f"📁 Saved {label} to {filename}")

def interactive_selection(prompt_template, count, label, preferred_gender_ratio=None):
    selections = []
    rejections = []
    male_count = 0
    female_count = 0
    while len(selections) < count:
        gender_bias_note = ""
        if preferred_gender_ratio:
            if female_count * 2 >= male_count:
                gender_bias_note = " The character should be male."
            else:
                gender_bias_note = " The character can be any gender."

        prompt = prompt_template.format(previous_rejected="\n".join(rejections)) + gender_bias_note
        suggestion = call_ollama(prompt).strip()
        print(f"\nSuggested {label} {len(selections)+1}:")
        print(suggestion)
        keep = input(f"Are you happy with this {label.lower()}? (y/n): ").strip().lower()
        if keep == 'y':
            selections.append(suggestion)
            save_entity(suggestion, f"{label}_{len(selections)}")
            if preferred_gender_ratio:
                if "female" in suggestion.lower():
                    female_count += 1
                elif "male" in suggestion.lower():
                    male_count += 1
        else:
            rejections.append(suggestion)
            print(f"Requesting a new {label.lower()}...\n")
    return selections

def generate_prompt(chapter_number, story_summary, book_summary, locations, main_characters, side_characters):
    char_cycle = (main_characters + side_characters)[(chapter_number - 1) % len(main_characters + side_characters)]
    image_prompt_note = f"[Image prompt: Generate an illustration with approximately {IMAGE_PROMPT_WORDS} words depicting the key visual scene or mood of this chapter.]"

    return f"""
You are writing Chapter {chapter_number} of a science fiction novel series.

Book summary:
{book_summary}

Story so far (summary):
{story_summary}

Main locations:
{chr(10).join(locations)}

Main characters:
{chr(10).join(main_characters)}

Side characters (who may die):
{chr(10).join(side_characters)}

This chapter should be told from the perspective of: {char_cycle}.

Write Chapter {chapter_number}. Each chapter is approximately {CHAPTER_WORDS} words.

{image_prompt_note}
"""

def save_chapter(book_number, chapter_number, text):
    filename = os.path.join(OUTPUT_DIR, f"book_{book_number:02d}_chapter_{chapter_number:02d}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ Book {book_number} Chapter {chapter_number:02d} saved: {filename}")
    return text

def create_epub(title, chapters):
    book = epub.EpubBook()
    book.set_identifier(str(uuid.uuid4()))
    book.set_title(title)
    book.set_language('en')
    book.add_author('AI Generated')

    epub_chapters = []
    for i, chapter_text in enumerate(chapters, 1):
        clean_text = chapter_text.split("[Image prompt:")[0].strip()
        c = epub.EpubHtml(title=f"Chapter {i}", file_name=f"chap_{i}.xhtml", lang='en')
        c.content = f'<h1>Chapter {i}</h1><p>{clean_text.replace("\n", "<br>")}</p>'
        book.add_item(c)
        epub_chapters.append(c)

    book.toc = tuple(epub_chapters)
    book.spine = ['nav'] + epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())

    epub.write_epub(EPUB_FILE, book)
    print(f"\n📘 EPUB file created: {EPUB_FILE}")

# --- Main ---
if __name__ == "__main__":
    print("\n🌌 Welcome to the Sci-Fi Series Generator 🌌\n")

    print("\nBefore we proceed, I have a few questions:")
    print("1. What is the overall tone of your science fiction story? Is it more focused on action, adventure, character development, or something else?")
    print("2. How do you see the crew dynamics playing out in your story? Will there be conflicts between characters, or will they work together seamlessly?")
    print("3. Are there any specific themes or ideas that you'd like to explore through these character concepts?\n")
    input("Press Enter when you're ready to begin character and location generation...")

    location_prompt = """
Suggest a unique and imaginative science fiction setting. Avoid any previously rejected ideas:
{previous_rejected}
"""
    main_char_prompt = """
Suggest a compelling main character for a science fiction story. Include their name, role, personality traits, gender, and a bit of backstory. Avoid any previously rejected ideas:
{previous_rejected}
"""
    side_char_prompt = """
Suggest a side character for a science fiction story. Include their name, role, personality traits, gender, and a brief note on why they might be expendable. Avoid any previously rejected ideas:
{previous_rejected}
"""

    print("\n📍 Let's choose 3 main locations.")
    locations = interactive_selection(location_prompt, 3, "Location")

    print("\n👤 Let's define 3 main characters (skewed 2:1 male:female).")
    main_characters = interactive_selection(main_char_prompt, 3, "Main Character", preferred_gender_ratio="2M:1F")

    print("\n🧍 Let's define 5 initial side characters (skewed 2:1 male:female).")
    side_characters = interactive_selection(side_char_prompt, 5, "Side Character", preferred_gender_ratio="2M:1F")

    full_story_text = ""
    chapter_texts = []

    for book_number in range(1, BOOK_COUNT + 1):
        story_summary = f"Summary from previous books up to Book {book_number - 1}." if book_number > 1 else ""
        book_summary = f"This is Book {book_number} in a continuing science fiction series."

        print(f"\n📚 Generating Book {book_number}...")

        for chapter_number in tqdm(range(1, CHAPTER_COUNT + 1), desc=f"📘 Book {book_number}", unit="chapter"):
            try:
                prompt = generate_prompt(chapter_number, story_summary, book_summary, locations, main_characters, side_characters)
                chapter_text = call_ollama(prompt)
                full_story_text += f"\n\n--- Book {book_number} Chapter {chapter_number} ---\n\n{chapter_text}"
                chapter_texts.append(chapter_text)
                save_chapter(book_number, chapter_number, chapter_text)
                time.sleep(DELAY_BETWEEN_CHAPTERS)
            except Exception as e:
                print(f"❌ Failed Book {book_number} Chapter {chapter_number}: {e}")

        if book_number < BOOK_COUNT:
            side_characters = interactive_selection(side_char_prompt, 5, "Side Character", preferred_gender_ratio="2M:1F")

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        f.write(full_story_text.strip())
    print(f"\n📘 Full story saved to {SUMMARY_FILE}")

    create_epub("Sci-Fi Series", chapter_texts)
    print("\n🎉 Series generation complete!\n")
