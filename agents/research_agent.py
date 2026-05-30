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

RESEARCH_PROMPT = """
You are a game research analyst. Your job is to thoroughly research a game concept before
any code is written. This is the most critical step — bad understanding leads to bad games.

The user wants to build: {concept}

You MUST research and provide ALL of the following sections. Be thorough and specific.

# Research Report: {concept}

## Game Type
Classify the game (e.g., "side-scrolling endless runner", "turn-based strategy board game",
"match-3 puzzle game"). Be specific.

## Core Mechanics (must have)
List every core mechanic that makes this game type work. These are NON-NEGOTIABLE —
if any are missing, the game won't feel right.
For each mechanic, explain briefly WHY it matters.

## Known Implementation Pitfalls
What are the hard problems that trip up developers building this type of game?
Be specific — mention data structures, algorithms, edge cases.
This section prevents the coding agent from being blindsided.

## Recommended Approach
Given that the output is a single HTML file using Phaser 3.js:
- What data structures should be used?
- What is the recommended architecture? (scene structure, state management)
- What Phaser APIs are most relevant?
- What should be drawn with graphics vs text vs sprites?

## Reference Patterns Found
Provide concrete code patterns or pseudocode for the trickiest parts.
For example:
- Board representation for chess: grid[row][col] = {{ type: 'king', color: 'white' }}
- Collision detection for platformers: AABB rectangle overlap
- Match-3 detection: flood fill from each cell

## Complexity Assessment
Rate the complexity (Simple / Moderate / Moderate-High / High / Very High).
Estimate the lines of code needed.
Identify the single hardest part and how much of the code budget it should get.

## Visual Design Recommendations
How should this game look when rendered with Phaser's Graphics API?
- What shapes, colors, gradients to use
- Screen size recommendation
- Font recommendations for text elements
- Background colour/style

Be thorough. The quality of the entire game depends on this research.
"""


def run(concept: str) -> str:
    print(f"[Research Agent] Researching: {concept}")

    prompt = RESEARCH_PROMPT.format(concept=concept)

    # Use Gemini with Google Search grounding for real-world research
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            safety_settings=SAFETY,
            tools=[types.Tool(google_search=types.GoogleSearch())],
            thinking_config=types.ThinkingConfig(thinking_budget=10000),
        ),
    )

    result = response.text

    os.makedirs("output", exist_ok=True)
    with open("output/research_report.md", "w", encoding="utf-8") as f:
        f.write(result)

    print("[Research Agent] Done. Written to output/research_report.md")
    return result


if __name__ == "__main__":
    run("dino runner game")
