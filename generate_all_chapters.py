import requests
import os
import time
from tqdm import tqdm

# --- CONFIGURATION ---
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"  # Change to your actual model name
CHAPTER_COUNT = 5
CHAPTER_WORDS = 500
OUTPUT_DIR = "chapters"
DELAY_BETWEEN_CHAPTERS = 5  # seconds

# --- SETUP ---
os.makedirs(OUTPUT_DIR, exist_ok=True)

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

def interactive_selection(prompt_template, count, label):
    selections = []
    for i in range(count):
        while True:
            prompt = prompt_template.format(previous_rejected="\n".join(selections))
            suggestion = call_ollama(prompt)
            print(f"\nSuggested {label} {i+1}:\n{suggestion}")
            keep = input(f"Are you happy with this {label.lower()}? (y/n): ").strip().lower()
            if keep == 'y':
                selections.append(suggestion.strip())
                break
            else:
                print(f"Requesting a new {label.lower()}...\n")
    return selections

def generate_prompt(chapter_number, story_so_far, locations, main_characters, side_characters):
    char_cycle = (main_characters + side_characters)[(chapter_number - 1) % len(main_characters + side_characters)]

    if chapter_number == 1:
        return f"""
You are writing the first chapter of a {CHAPTER_COUNT}-chapter science fiction novel. This is Chapter 1.

Main locations:
{chr(10).join(locations)}

Main characters:
{chr(10).join(main_characters)}

Side characters (who may die):
{chr(10).join(side_characters)}

This chapter should be told from the perspective of: {char_cycle}.

Please write approximately {CHAPTER_WORDS} words. Introduce:
- The main setting (sci-fi world or future scenario)
- Main characters
- Conflict or mystery to be explored

End the chapter with a hook that leads into Chapter 2.
Begin now:
"""
    elif chapter_number == CHAPTER_COUNT:
        return f"""
You are writing the final chapter (Chapter {chapter_number}) of a {CHAPTER_COUNT}-chapter science fiction novel.

Here is the story so far:
{story_so_far}

This chapter should be told from the perspective of: {char_cycle}.

This chapter should bring the story to a satisfying and coherent conclusion. Resolve all major plotlines and character arcs. Maintain the established tone and pacing.

Each chapter is approximately {CHAPTER_WORDS} words.

Write Chapter {chapter_number} now:
"""
    else:
        return f"""
You are writing Chapter {chapter_number} of a {CHAPTER_COUNT}-chapter science fiction novel.

Here is the story so far:
{story_so_far}

This chapter should be told from the perspective of: {char_cycle}.

Continue from the end of Chapter {chapter_number - 1}. Make sure the tone, characters, and setting remain consistent. Expand the plot, deepen character arcs, and build tension.

Each chapter is approximately {CHAPTER_WORDS} words.

Write Chapter {chapter_number} in full now:
"""

def save_chapter(chapter_number, text):
    filename = os.path.join(OUTPUT_DIR, f"chapter_{chapter_number:02d}.txt")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ Chapter {chapter_number:02d} saved: {filename}")

if __name__ == "__main__":
    print("\n🌌 Welcome to the Sci-Fi Story Generator 🌌\n")

    # Step 1: Locations
    print("\n📍 Let's choose 3 main locations for your story.")
    location_prompt = """
Suggest a unique and imaginative science fiction setting. Avoid any previously rejected ideas:
{previous_rejected}
"""
    locations = interactive_selection(location_prompt, 3, "Location")

    # Step 2: Main Characters
    print("\n👤 Now let's define 3 main characters.")
    main_char_prompt = """
Suggest a compelling main character for a science fiction story. Include their name, role, personality traits, and a bit of backstory. Avoid any previously rejected ideas:
{previous_rejected}
"""
    main_characters = interactive_selection(main_char_prompt, 3, "Main Character")

    # Step 3: Side Characters
    print("\n🧍 Now let's define 5 side characters who could possibly die.")
    side_char_prompt = """
Suggest a side character for a science fiction story. Include their name, role, and a brief note on why they might be expendable. Avoid any previously rejected ideas:
{previous_rejected}
"""
    side_characters = interactive_selection(side_char_prompt, 5, "Side Character")

    # Story Generation
    story_so_far = ""
    chapter_range = range(1, CHAPTER_COUNT + 1)

    print(f"\n🚀 Starting generation of {CHAPTER_COUNT} chapters...\n")

    for chapter_number in tqdm(chapter_range, desc="📘 Generating Chapters", unit="chapter"):
        print(f"\n📘 Generating Chapter {chapter_number:02d}...")
        start_time = time.time()

        try:
            prompt = generate_prompt(chapter_number, story_so_far, locations, main_characters, side_characters)
            chapter_text = call_ollama(prompt)
            save_chapter(chapter_number, chapter_text)
            story_so_far += f"\n\n--- Chapter {chapter_number} ---\n\n{chapter_text}"
            elapsed = time.time() - start_time
            print(f"⏱️ Time taken for Chapter {chapter_number:02d}: {elapsed:.2f} seconds")
        except Exception as e:
            print(f"❌ Failed to generate Chapter {chapter_number}: {e}")

        if chapter_number != CHAPTER_COUNT:
            time.sleep(DELAY_BETWEEN_CHAPTERS)

    print("\n🎉 All chapters generated!\n")
