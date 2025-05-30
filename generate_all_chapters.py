import requests
import os
import time

# --- CONFIGURATION ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"  # Change to your actual model name
CHAPTER_COUNT = 12
CHAPTER_WORDS = 1000
OUTPUT_DIR = "chapters"
DELAY_BETWEEN_CHAPTERS = 5  # seconds

# --- SETUP ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_prompt(chapter_number):
    if chapter_number == 1:
        return f"""
You are writing the first chapter of a 12-chapter science fiction novel. This is Chapter 1.

Please write approximately {CHAPTER_WORDS} words. Introduce:
- The main setting (sci-fi world or future scenario)
- Main characters
- Conflict or mystery to be explored

End the chapter with a hook that leads into Chapter 2.
Begin now:
"""
    else:
        return f"""
You are writing Chapter {chapter_number} of a 12-chapter science fiction novel.

Continue from the end of Chapter {chapter_number - 1}. Make sure the tone, characters, and setting remain consistent. Expand the plot, deepen character arcs, and build tension.

Each chapter is approximately {CHAPTER_WORDS} words.

Write Chapter {chapter_number} in full now:
"""

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

def save_chapter(chapter_number, text):
    filename = os.path.join(OUTPUT_DIR, f"chapter_{chapter_number:02d}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ Chapter {chapter_number:02d} saved: {filename}")

# --- MAIN LOOP ---
if __name__ == "__main__":
    for chapter_number in range(1, CHAPTER_COUNT + 1):
        print(f"📘 Generating Chapter {chapter_number:02d}...")
        try:
            prompt = generate_prompt(chapter_number)
            chapter_text = call_ollama(prompt)
            save_chapter(chapter_number, chapter_text)
        except Exception as e:
            print(f"❌ Failed to generate Chapter {chapter_number}: {e}")
        if chapter_number != CHAPTER_COUNT:
            time.sleep(DELAY_BETWEEN_CHAPTERS)
