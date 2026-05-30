import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SAFETY = [
    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="BLOCK_NONE"),
    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="BLOCK_NONE"),
]

PROMPT_TEMPLATE = """
You are a game designer specialising in HTML5 browser games built with Phaser 3.js.

Based on the user's game concept AND the research report below, write a detailed game design document.

Game concept: {concept}

--- RESEARCH REPORT ---
{research_report}

Your output must follow this exact structure with these exact headings:

# Game Design Document

## Characters
Describe the main character and any enemies or NPCs.
Be specific about how each character will be DRAWN using Phaser's Graphics API:
- What shapes (rectangles, circles, triangles, lines)
- What colours (hex codes)
- What size in pixels
- What animation states they need (idle, moving, attacking, etc.)

## Story
A short 2-3 sentence backstory for the game.

## Core Mechanics
Based on the research, list every mechanic that MUST be implemented for the game to work.
For each mechanic, briefly describe how it works in gameplay terms.
Do NOT skip any mechanic listed as "must have" in the research report.

## Level Progression
Describe how difficulty increases over time (speed, obstacles, enemies, complexity).
Reference specific parameters and thresholds.

## Visual Theme
Describe the art style using ONLY what Phaser's Graphics API can draw:
- Shapes (rectangles, circles, lines, polygons)
- Gradients and colour fills (use hex codes)
- Text objects with specific fonts and sizes
- NO external images — everything is drawn in code
Specify the screen dimensions and background colour.

## Audio Design
Describe what sound effects and music are needed.
These will be generated using the Web Audio API (oscillators, envelopes).
Describe each sound by its characteristics:
- Frequency (low/mid/high)
- Duration (short/medium/long)
- Style (rising, falling, beep, sweep, noise burst)

Keep the entire document concise and practical. This will be used by a coding agent
to build a complete Phaser 3.js game in a single HTML file.
"""


def run(concept: str, research_report: str = None) -> str:
    print(f"[Script Agent] Running with concept: {concept}")

    if research_report is None:
        report_path = "output/research_report.md"
        if os.path.exists(report_path):
            with open(report_path, "r", encoding="utf-8") as f:
                research_report = f.read()
        else:
            research_report = "(No research report available — design from general knowledge)"

    prompt = PROMPT_TEMPLATE.format(concept=concept, research_report=research_report)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            safety_settings=SAFETY,
            thinking_config=types.ThinkingConfig(thinking_budget=5000),
        ),
    )

    result = response.text

    os.makedirs("output", exist_ok=True)
    with open("output/game_design.md", "w", encoding="utf-8") as f:
        f.write(result)

    print("[Script Agent] Done. Written to output/game_design.md")
    return result


if __name__ == "__main__":
    run("dino runner game")