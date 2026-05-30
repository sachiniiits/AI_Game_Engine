"""
Game Generator Pipeline V2 — Research-First, Phaser.js

Runs all 5 agents in sequence:
  1. Research Agent  → output/research_report.md
  2. Script Agent    → output/game_design.md
  3. Logic Agent     → output/pseudocode.md + output/draw_manifest.md
  4. Coding Agent    → build/web/game.html
  5. Validator Agent  → output/validation_report.md
     ↳ On failure, retries Coding Agent (max 3 attempts)

Usage:
  python pipeline.py "make a snake game"
  python pipeline.py  (prompts for input)
"""

import sys
import os
import time

# Add project root to path so agents can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import research_agent, script_agent, logic_agent, coding_agent, validator_agent

MAX_RETRIES = 3


def run_pipeline(concept: str) -> str:
    """Run the full V2 pipeline and return the path to the generated game."""
    print("=" * 60)
    print("  GAME GENERATOR PIPELINE V2")
    print("  Research-First | Phaser.js | Single HTML Output")
    print("=" * 60)
    print(f"\n  Game concept: {concept}\n")
    print("=" * 60)

    total_start = time.time()

    # --- Agent 1: Research ---
    print("\n" + "-" * 60)
    print("  PHASE 1/5 -- Research Agent")
    print("-" * 60)
    start = time.time()
    research_report = research_agent.run(concept)
    print(f"  [TIME] Research completed in {time.time() - start:.1f}s")

    # --- Agent 2: Script (Game Design) ---
    print("\n" + "-" * 60)
    print("  PHASE 2/5 -- Script Agent (Game Design)")
    print("-" * 60)
    start = time.time()
    game_design = script_agent.run(concept, research_report)
    print(f"  [TIME] Game design completed in {time.time() - start:.1f}s")

    # --- Agent 3: Logic (Pseudocode + Draw Manifest) ---
    print("\n" + "-" * 60)
    print("  PHASE 3/5 -- Logic Agent (Pseudocode + Draw Manifest)")
    print("-" * 60)
    start = time.time()
    pseudocode, draw_manifest = logic_agent.run(game_design)
    print(f"  [TIME] Logic completed in {time.time() - start:.1f}s")

    # --- Agent 4 + 5: Coding + Validation (with retry loop) ---
    print("\n" + "-" * 60)
    print("  PHASE 4-5/5 -- Coding Agent + Validator (retry loop)")
    print("-" * 60)

    retry_feedback = None
    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n  --- Attempt {attempt}/{MAX_RETRIES} ---")

        # Coding Agent
        start = time.time()
        code = coding_agent.run(
            game_design=game_design,
            pseudocode=pseudocode,
            draw_manifest=draw_manifest,
            retry_feedback=retry_feedback,
        )
        print(f"  [TIME] Coding completed in {time.time() - start:.1f}s")

        # Validator Agent
        start = time.time()
        passed, feedback = validator_agent.run(code)
        print(f"  [TIME] Validation completed in {time.time() - start:.1f}s")

        if passed:
            print(f"\n  [PASS] Game passed validation on attempt {attempt}")
            break
        else:
            print(f"\n  [FAIL] Validation failed on attempt {attempt}")
            print(f"  Errors:\n    {feedback.replace(chr(10), chr(10) + '    ')}")
            retry_feedback = feedback

            if attempt == MAX_RETRIES:
                print(f"\n  [WARN] Max retries ({MAX_RETRIES}) reached. Game may have issues.")

    # --- Summary ---
    total_time = time.time() - total_start
    output_path = os.path.abspath("build/web/game.html")

    print("\n" + "=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Total time: {total_time:.1f}s")
    print(f"  Status: {'PASSED' if passed else 'FAILED (best effort saved)'}")
    print(f"\n  Generated files:")
    print(f"    - output/research_report.md")
    print(f"    - output/game_design.md")
    print(f"    - output/pseudocode.md")
    print(f"    - output/draw_manifest.md")
    print(f"    - output/validation_report.md")
    print(f"    - build/web/game.html  <-- THE GAME")
    print(f"\n  Open in browser to play:")
    print(f"    {output_path}")
    print("=" * 60)

    return output_path


if __name__ == "__main__":
    if len(sys.argv) > 1:
        concept = " ".join(sys.argv[1:])
    else:
        concept = input("Enter your game concept: ").strip()
        if not concept:
            print("Error: No game concept provided.")
            sys.exit(1)

    run_pipeline(concept)
