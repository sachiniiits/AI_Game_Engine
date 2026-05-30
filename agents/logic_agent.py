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

PSEUDOCODE_PROMPT = """
You are a game developer specialising in Phaser 3.js HTML5 games.

Based on this game design document, write complete pseudocode for a Phaser 3 game.

{game_design}

Your output must follow this exact structure:

# Pseudocode

## Phaser Scene Structure
Describe the Phaser.Scene subclass with these lifecycle methods:
- preload(): what needs to be loaded (fonts, etc.) — usually empty since we draw everything
- create(): initialise all game objects, set up input handlers, create graphics
- update(time, delta): called every frame — game logic goes here

## Game State Machine
List all possible states and transitions:
STATE = {{ MENU, PLAYING, PAUSED, GAME_OVER }}
Describe what triggers each transition.

## create() Breakdown
Step by step, what happens when the scene starts:
- What graphics objects are created (this.add.graphics())
- What text objects are created (this.add.text())
- What input handlers are set up (keyboard, mouse/touch)
- What data structures are initialised
- What timers or events are scheduled

## update() Breakdown
Step by step, what happens every frame:
- Check game state — skip logic if not PLAYING
- Handle input (keyboard/mouse state)
- Update positions and physics
- Check collisions
- Update score/timer
- Check win/lose conditions
- Update visual elements

## Input Handling
Detail every input the game accepts:
- What keys do what (SPACE, ARROW keys, R for restart, etc.)
- What mouse/touch actions do what (click, drag, etc.)
- How input maps to game actions

## Draw Functions
What gets drawn each frame and in what order (back to front):
- Background
- Game board / play area
- Game objects (player, enemies, items)
- UI overlay (score, lives, timer)
- State-specific overlays (menu screen, game over screen)

## Collision / Interaction Logic
How do game objects interact with each other:
- What collision detection method is used
- What happens on each type of collision
- Edge cases and special interactions

Keep it detailed enough that a coding agent can translate it directly to Phaser 3 JavaScript.
Every function and data structure should be described.
"""

DRAW_MANIFEST_PROMPT = """
You are a visual designer for Phaser 3.js HTML5 games.

Based on this game design document, create a complete draw manifest.
This describes EVERYTHING that needs to be drawn — all using Phaser's built-in APIs, NO external images.

{game_design}

Your output must follow this exact structure:

# Draw Manifest

## Visual Elements (all drawn in code, no image files)
For each visual element, specify:
- Name: (e.g., "player", "enemy_type_1", "background")
- Draw method: (this.add.graphics() shapes, this.add.text(), etc.)
- Shape: (rectangle, circle, polygon, line, etc.)
- Colours: (hex codes for fill and stroke)
- Size: (width x height in pixels)
- Position: (where on screen, or relative to what)
- Animation: (how it changes over time, if at all)

## Fonts
- What fonts are used (built-in sans-serif, or Google Fonts if needed)
- Size for each text element
- Colour for each text element

## Screen Layout
- Total screen size: WIDTHxHEIGHT
- Background colour: #HEXCODE
- Describe the layout zones (game area, HUD area, sidebar, etc.)

## Colour Palette
List every colour used in the game with:
- Hex code
- What it's used for
- Any alpha/opacity variations

## State-Specific Visuals
What changes visually in each game state:
- MENU: what the menu screen looks like
- PLAYING: the main game view
- GAME_OVER: the game over overlay

Rules:
- NO external images — everything is drawn with Phaser Graphics API
- NO external fonts unless absolutely necessary
- Keep the colour palette cohesive (max 8-10 colours)
- All sizes must be specific pixel values
"""


def run(game_design: str = None) -> tuple[str, str]:
    if game_design is None:
        with open("output/game_design.md", "r", encoding="utf-8") as f:
            game_design = f.read()

    print("[Logic Agent] Generating Phaser-aware pseudocode...")
    pseudocode_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=PSEUDOCODE_PROMPT.format(game_design=game_design),
        config=types.GenerateContentConfig(
            safety_settings=SAFETY,
            thinking_config=types.ThinkingConfig(thinking_budget=5000),
        ),
    )
    pseudocode = pseudocode_response.text

    print("[Logic Agent] Generating draw manifest...")
    manifest_response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=DRAW_MANIFEST_PROMPT.format(game_design=game_design),
        config=types.GenerateContentConfig(
            safety_settings=SAFETY,
            thinking_config=types.ThinkingConfig(thinking_budget=5000),
        ),
    )
    draw_manifest = manifest_response.text

    os.makedirs("output", exist_ok=True)
    with open("output/pseudocode.md", "w", encoding="utf-8") as f:
        f.write(pseudocode)

    with open("output/draw_manifest.md", "w", encoding="utf-8") as f:
        f.write(draw_manifest)

    print("[Logic Agent] Done. Written to output/pseudocode.md and output/draw_manifest.md")
    return pseudocode, draw_manifest


if __name__ == "__main__":
    run()