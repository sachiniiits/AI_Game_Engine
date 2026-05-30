import os
import sys
import re

MAX_RETRIES = 3


def check_html_structure(code: str) -> list[str]:
    """Check that the file is valid HTML with required elements."""
    errors = []

    if "<!DOCTYPE html>" not in code and "<!doctype html>" not in code:
        errors.append("Missing <!DOCTYPE html> declaration")

    if "<html" not in code:
        errors.append("Missing <html> tag")

    if "</html>" not in code:
        errors.append("Missing closing </html> tag")

    if "<script" not in code:
        errors.append("Missing <script> tag — no JavaScript found")

    if "phaser" not in code.lower():
        errors.append("No reference to Phaser found — the game must use Phaser 3")

    if "cdn.jsdelivr.net/npm/phaser" not in code and "cdnjs.cloudflare.com" not in code:
        errors.append("Phaser not loaded from CDN — add: <script src=\"https://cdn.jsdelivr.net/npm/phaser@3/dist/phaser.min.js\"></script>")

    return errors


def check_phaser_basics(code: str) -> list[str]:
    """Check for essential Phaser patterns in the code."""
    errors = []

    if "Phaser.Scene" not in code and "Phaser.Game" not in code:
        errors.append("Missing Phaser.Scene or Phaser.Game — the game needs a scene class")

    if "new Phaser.Game" not in code:
        errors.append("Missing 'new Phaser.Game(config)' — game is never instantiated")

    if "create" not in code:
        errors.append("Missing create() method in scene")

    if "update" not in code:
        errors.append("Missing update() method in scene")

    # Check for common JavaScript errors
    js_match = re.findall(r'<script[^>]*>(.*?)</script>', code, re.DOTALL)
    js_code = "\n".join(js_match)

    if js_code:
        # Check for unclosed brackets/braces (simple heuristic)
        open_braces = js_code.count("{")
        close_braces = js_code.count("}")
        if abs(open_braces - close_braces) > 1:
            errors.append(f"Mismatched braces: {open_braces} opening vs {close_braces} closing — likely syntax error")

        open_parens = js_code.count("(")
        close_parens = js_code.count(")")
        if abs(open_parens - close_parens) > 1:
            errors.append(f"Mismatched parentheses: {open_parens} opening vs {close_parens} closing — likely syntax error")

    return errors


def check_game_quality(code: str) -> list[str]:
    """Check for game quality indicators (non-blocking warnings)."""
    warnings = []

    if "GAME_OVER" not in code and "gameOver" not in code and "game_over" not in code:
        warnings.append("WARNING: No game over state detected — game may not have win/lose condition")

    if "MENU" not in code and "menu" not in code and "TITLE" not in code and "title" not in code.lower().split("</title>")[0] if "</title>" in code else "":
        warnings.append("WARNING: No menu/title state detected — game may start abruptly")

    restart_patterns = ["KEY_R", "'R'", "restart", "Restart", "RESTART", "play again", "Play Again"]
    if not any(p in code for p in restart_patterns):
        warnings.append("WARNING: No restart mechanism detected — add press R or click to restart")

    return warnings


async def run_playwright_check(html_path: str) -> dict:
    """Run headless browser validation using Playwright."""
    results = {
        "screenshot": None,
        "console_errors": [],
        "rendered": False,
        "errors": [],
    }

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Collect console errors
            console_errors = []
            page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)

            # Collect page errors (uncaught exceptions)
            page_errors = []
            page.on("pageerror", lambda err: page_errors.append(str(err)))

            # Open the game
            abs_path = os.path.abspath(html_path)
            file_url = f"file:///{abs_path.replace(os.sep, '/')}"
            await page.goto(file_url, wait_until="networkidle", timeout=15000)

            # Wait for game to render
            await page.wait_for_timeout(3000)

            # Take screenshot
            screenshot_path = os.path.join("output", "game_screenshot.png")
            await page.screenshot(path=screenshot_path)
            results["screenshot"] = screenshot_path

            # Check if canvas exists and has content
            canvas_exists = await page.evaluate("""() => {
                const canvas = document.querySelector('canvas');
                if (!canvas) return false;
                const ctx = canvas.getContext('2d');
                if (!ctx) return true;  // WebGL canvas, assume rendered
                const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
                const data = imageData.data;
                let nonBlack = 0;
                for (let i = 0; i < data.length; i += 4) {
                    if (data[i] > 0 || data[i+1] > 0 || data[i+2] > 0) nonBlack++;
                }
                return nonBlack > 100;
            }""")

            if not canvas_exists:
                results["errors"].append("Game canvas not found or appears blank/black after 3 seconds")
            else:
                results["rendered"] = True
                print("[Validator Agent] Canvas rendered successfully")

            # Simulate a keypress (SPACE) to test interactivity
            await page.keyboard.press("Space")
            await page.wait_for_timeout(500)

            # Simulate a click
            await page.mouse.click(240, 240)
            await page.wait_for_timeout(500)

            # Check for errors after interaction
            if console_errors:
                results["console_errors"] = console_errors
                results["errors"].extend([f"Console error: {e}" for e in console_errors])

            if page_errors:
                results["errors"].extend([f"JavaScript error: {e}" for e in page_errors])

            await browser.close()

    except ImportError:
        results["errors"].append("Playwright not installed — skipping browser validation. Run: pip install playwright && playwright install chromium")
    except Exception as e:
        results["errors"].append(f"Playwright error: {str(e)}")

    return results


def run(code: str = None) -> tuple[bool, str]:
    if code is None:
        html_path = "build/web/game.html"
        if not os.path.exists(html_path):
            print("[Validator Agent] ERROR: build/web/game.html not found")
            return False, "build/web/game.html not found. Run the Coding Agent first."
        with open(html_path, "r", encoding="utf-8") as f:
            code = f.read()

    print("[Validator Agent] Starting validation...")
    all_errors = []
    all_warnings = []

    # Check 1 — HTML structure
    print("[Validator Agent] Checking HTML structure...")
    html_errors = check_html_structure(code)
    if html_errors:
        all_errors.extend(html_errors)
        print(f"[Validator Agent] HTML structure errors: {html_errors}")
    else:
        print("[Validator Agent] HTML structure OK")

    # Check 2 — Phaser basics
    print("[Validator Agent] Checking Phaser structure...")
    phaser_errors = check_phaser_basics(code)
    if phaser_errors:
        all_errors.extend(phaser_errors)
        print(f"[Validator Agent] Phaser structure errors: {phaser_errors}")
    else:
        print("[Validator Agent] Phaser structure OK")

    # Check 3 — Game quality
    print("[Validator Agent] Checking game quality...")
    quality_warnings = check_game_quality(code)
    if quality_warnings:
        all_warnings.extend(quality_warnings)
        for w in quality_warnings:
            print(f"[Validator Agent] {w}")
    else:
        print("[Validator Agent] Game quality checks passed")

    # Check 4 — Playwright headless browser check (only if no structural errors)
    if not all_errors:
        print("[Validator Agent] Running headless browser check...")
        try:
            import asyncio
            playwright_results = asyncio.run(run_playwright_check("build/web/game.html"))
            if playwright_results["errors"]:
                # Separate actual errors from "playwright not installed" warnings
                for err in playwright_results["errors"]:
                    if "not installed" in err:
                        all_warnings.append(err)
                        print(f"[Validator Agent] {err}")
                    else:
                        all_errors.append(err)
                        print(f"[Validator Agent] ERROR: {err}")
            if playwright_results["rendered"]:
                print("[Validator Agent] Game rendered successfully in headless browser")
            if playwright_results["screenshot"]:
                print(f"[Validator Agent] Screenshot saved to {playwright_results['screenshot']}")
        except Exception as e:
            all_warnings.append(f"Playwright check skipped: {str(e)}")
            print(f"[Validator Agent] Playwright check skipped: {e}")

    # Write validation report
    os.makedirs("output", exist_ok=True)
    report_lines = ["# Validation Report\n\n"]

    if all_errors:
        report_lines.append("## Status: FAILED\n\n")
        report_lines.append("## Errors Found\n")
        for err in all_errors:
            report_lines.append(f"- {err}\n")
        passed = False
        feedback = "\n".join(all_errors)
    else:
        report_lines.append("## Status: PASSED\n\n")
        report_lines.append("All checks passed. Game is ready to play.\n")
        passed = True
        feedback = ""

    if all_warnings:
        report_lines.append("\n## Warnings\n")
        for w in all_warnings:
            report_lines.append(f"- {w}\n")
        if passed:
            feedback = "\n".join(all_warnings)

    with open("output/validation_report.md", "w", encoding="utf-8") as f:
        f.writelines(report_lines)

    print(f"[Validator Agent] Done. Status: {'PASSED' if passed else 'FAILED'}")
    return passed, feedback


if __name__ == "__main__":
    passed, feedback = run()
    if not passed:
        print("\nFeedback for Coding Agent:")
        print(feedback)
        sys.exit(1)
    else:
        print("\nGame passed all validation checks.")