import os
import requests
import json

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:latest"

BIBLE_TXT_FILE = "narrative_bible.txt"
BIBLE_JSON_FILE = "narrative_bible.json"

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

    # Optionally parse to JSON (simple heuristic structure)
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

def main():
    print("Generating narrative bible...")
    output = query_ollama(PROMPT)
    save_outputs(output)

if __name__ == "__main__":
    main()
