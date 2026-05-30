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

# Phaser API quick reference injected into every prompt (Fix #1 from roadmap)
PHASER_API_REFERENCE = """
--- PHASER 3 API REFERENCE (use only these) ---
SCENE LIFECYCLE:
- class MyScene extends Phaser.Scene { constructor() { super({ key: 'MyScene' }); } }
- preload() — load assets (usually empty when drawing everything in code)
- create() — initialise game objects, input, graphics
- update(time, delta) — called every frame, game logic goes here

GRAPHICS (this.add.graphics()):
- graphics.fillStyle(0xRRGGBB, alpha) — set fill colour
- graphics.fillRect(x, y, w, h) — draw filled rectangle
- graphics.fillCircle(x, y, radius) — draw filled circle
- graphics.fillTriangle(x1,y1, x2,y2, x3,y3) — draw filled triangle
- graphics.fillRoundedRect(x, y, w, h, radius) — rounded rectangle
- graphics.lineStyle(width, 0xRRGGBB, alpha) — set line style
- graphics.strokeRect(x, y, w, h) — draw rectangle outline
- graphics.strokeCircle(x, y, radius) — draw circle outline
- graphics.lineBetween(x1, y1, x2, y2) — draw line
- graphics.clear() — clear all drawings from this graphics object
- graphics.setDepth(n) — set render layer order

TEXT (this.add.text()):
- this.add.text(x, y, 'string', { fontSize: '18px', fontFamily: 'Arial', fill: '#ffffff' })
- text.setText('new string') — update text content
- text.setOrigin(0.5) — center the text
- text.setDepth(n) — set render layer order
- text.setVisible(bool) — show/hide

INPUT:
- this.input.keyboard.addKey('SPACE') — returns Key object
- this.input.keyboard.createCursorKeys() — returns { up, down, left, right, space, shift }
- key.isDown — boolean, true while held
- Phaser.Input.Keyboard.JustDown(key) — true only on first frame of press
- this.input.on('pointerdown', callback) — mouse/touch click
- this.input.activePointer.x / .y — mouse position

PHYSICS (this.physics — if using Arcade physics):
- this.physics.add.sprite(x, y, key) — physics sprite
- sprite.setVelocityX(n) / .setVelocityY(n) — set velocity
- sprite.setBounce(n) — set bounce factor
- sprite.setCollideWorldBounds(true) — keep in screen
- this.physics.add.collider(obj1, obj2, callback) — collision detection
- this.physics.add.overlap(obj1, obj2, callback) — overlap detection

TWEENS & TIMERS:
- this.tweens.add({ targets, x, y, duration, ease, onComplete }) — animation
- this.time.addEvent({ delay, callback, loop, repeat }) — timer
- this.time.delayedCall(delay, callback) — one-shot timer

GAME CONFIG:
- type: Phaser.AUTO — auto-detect Canvas or WebGL
- width, height — game dimensions
- backgroundColor: '#HEXCODE' — background colour
- physics: { default: 'arcade', arcade: { gravity: { y: N }, debug: false } }
- scene: [MyScene] — array of scene classes
"""

# Working mini-examples per game type (Fix #2 from roadmap)
GAME_EXAMPLES = {
    "platformer": """
--- WORKING PHASER PLATFORMER SNIPPET ---
create() {
    this.platforms = this.physics.add.staticGroup();
    this.platforms.create(240, 460, null).setDisplaySize(480, 20).refreshBody();
    this.player = this.add.rectangle(100, 400, 20, 30, 0x00ff00);
    this.physics.add.existing(this.player);
    this.player.body.setCollideWorldBounds(true);
    this.player.body.setBounce(0.1);
    this.physics.add.collider(this.player, this.platforms);
    this.cursors = this.input.keyboard.createCursorKeys();
}
update() {
    if (this.cursors.left.isDown) this.player.body.setVelocityX(-160);
    else if (this.cursors.right.isDown) this.player.body.setVelocityX(160);
    else this.player.body.setVelocityX(0);
    if (this.cursors.up.isDown && this.player.body.touching.down) this.player.body.setVelocityY(-300);
}
""",
    "chess": """
--- WORKING PHASER CHESS BOARD SNIPPET ---
create() {
    const boardSize = 400, squareSize = boardSize / 8;
    const lightColor = 0xF0D9B5, darkColor = 0xB58863;
    this.boardGfx = this.add.graphics();
    for (let row = 0; row < 8; row++) {
        for (let col = 0; col < 8; col++) {
            const color = (row + col) % 2 === 0 ? lightColor : darkColor;
            this.boardGfx.fillStyle(color, 1);
            this.boardGfx.fillRect(col * squareSize, row * squareSize, squareSize, squareSize);
        }
    }
    const pieces = '♜♞♝♛♚♝♞♜';
    for (let col = 0; col < 8; col++) {
        this.add.text(col * squareSize + squareSize/2, squareSize/2, pieces[col],
            { fontSize: '28px', fill: '#1a1a1a' }).setOrigin(0.5);
    }
}
""",
    "snake": """
--- WORKING PHASER SNAKE SNIPPET ---
create() {
    this.gridSize = 20;
    this.snake = [{ x: 5, y: 5 }];
    this.direction = { x: 1, y: 0 };
    this.food = { x: 10, y: 10 };
    this.gfx = this.add.graphics();
    this.moveTimer = 0;
    this.cursors = this.input.keyboard.createCursorKeys();
}
update(time, delta) {
    if (this.cursors.left.isDown && this.direction.x !== 1) this.direction = { x: -1, y: 0 };
    if (this.cursors.right.isDown && this.direction.x !== -1) this.direction = { x: 1, y: 0 };
    if (this.cursors.up.isDown && this.direction.y !== 1) this.direction = { x: 0, y: -1 };
    if (this.cursors.down.isDown && this.direction.y !== -1) this.direction = { x: 0, y: 1 };
    this.moveTimer += delta;
    if (this.moveTimer > 150) {
        this.moveTimer = 0;
        const head = { x: this.snake[0].x + this.direction.x, y: this.snake[0].y + this.direction.y };
        this.snake.unshift(head);
        if (head.x === this.food.x && head.y === this.food.y) {
            this.food = { x: Math.floor(Math.random() * 20), y: Math.floor(Math.random() * 20) };
        } else { this.snake.pop(); }
    }
    this.gfx.clear();
    this.gfx.fillStyle(0x00ff00, 1);
    this.snake.forEach(s => this.gfx.fillRect(s.x * this.gridSize, s.y * this.gridSize, this.gridSize - 1, this.gridSize - 1));
    this.gfx.fillStyle(0xff0000, 1);
    this.gfx.fillRect(this.food.x * this.gridSize, this.food.y * this.gridSize, this.gridSize - 1, this.gridSize - 1);
}
""",
    "runner": """
--- WORKING PHASER ENDLESS RUNNER SNIPPET ---
create() {
    this.ground = this.add.rectangle(240, 460, 480, 40, 0x8B4513);
    this.physics.add.existing(this.ground, true);
    this.player = this.add.rectangle(60, 420, 20, 30, 0x00ff00);
    this.physics.add.existing(this.player);
    this.player.body.setCollideWorldBounds(true);
    this.physics.add.collider(this.player, this.ground);
    this.obstacles = this.physics.add.group();
    this.physics.add.collider(this.obstacles, this.ground);
    this.physics.add.overlap(this.player, this.obstacles, () => { this.gameState = 'GAME_OVER'; });
    this.spaceKey = this.input.keyboard.addKey('SPACE');
    this.spawnTimer = this.time.addEvent({ delay: 1500, callback: this.spawnObstacle, callbackScope: this, loop: true });
}
spawnObstacle() {
    const obs = this.add.rectangle(500, 440, 15, 25, 0xff0000);
    this.physics.add.existing(obs);
    obs.body.setVelocityX(-200);
    this.obstacles.add(obs);
}
update() {
    if (Phaser.Input.Keyboard.JustDown(this.spaceKey) && this.player.body.touching.down) {
        this.player.body.setVelocityY(-350);
    }
}
""",
    "puzzle": """
--- WORKING PHASER GRID PUZZLE SNIPPET ---
create() {
    this.gridSize = 6;
    this.cellSize = 60;
    this.colors = [0xff0000, 0x00ff00, 0x0000ff, 0xffff00, 0xff00ff];
    this.grid = [];
    this.gfx = this.add.graphics();
    for (let r = 0; r < this.gridSize; r++) {
        this.grid[r] = [];
        for (let c = 0; c < this.gridSize; c++) {
            this.grid[r][c] = this.colors[Math.floor(Math.random() * this.colors.length)];
        }
    }
    this.drawGrid();
    this.input.on('pointerdown', (pointer) => {
        const col = Math.floor(pointer.x / this.cellSize);
        const row = Math.floor(pointer.y / this.cellSize);
        if (row >= 0 && row < this.gridSize && col >= 0 && col < this.gridSize) {
            this.handleClick(row, col);
        }
    });
}
drawGrid() {
    this.gfx.clear();
    for (let r = 0; r < this.gridSize; r++) {
        for (let c = 0; c < this.gridSize; c++) {
            this.gfx.fillStyle(this.grid[r][c], 1);
            this.gfx.fillRect(c * this.cellSize + 2, r * this.cellSize + 2, this.cellSize - 4, this.cellSize - 4);
        }
    }
}
""",
}

PROMPT_TEMPLATE = """
You are an expert JavaScript game developer who specialises in Phaser 3.

Write a complete, working Phaser 3 game as a SINGLE self-contained HTML file.

--- GAME DESIGN ---
{game_design}

--- PSEUDOCODE ---
{pseudocode}

--- DRAW MANIFEST ---
{draw_manifest}

{phaser_api_reference}

{game_example}

--- STRICT RULES ---
1. Output ONE complete HTML file and NOTHING else. No explanations, no markdown, no backticks.
2. The HTML must start with <!DOCTYPE html> and end with </html>.
3. Import Phaser from CDN: <script src="https://cdn.jsdelivr.net/npm/phaser@3/dist/phaser.min.js"></script>
4. All drawing done with Phaser Graphics API — NO external images, NO image loading.
5. All audio done with Web Audio API (AudioContext, OscillatorNode) — NO external sound files.
6. Use Phaser.Scene with preload(), create(), update() structure.
7. Use this.add.graphics() for shapes, this.add.text() for text.
8. Handle both keyboard and mouse/touch input.
9. Game must be fully playable and bug-free.
10. Include a restart mechanism (press R or click button on game over).
11. Screen size: 480x480 unless the game needs different proportions.
12. Include a MENU state with the game title and "Press SPACE to Start" or click-to-start.
13. Include a GAME_OVER state with final score and restart instructions.
14. Use smooth animations and transitions — the game should feel polished.
15. Centre the canvas on the page with a dark background (#1a1a2e or similar).
16. Add a <title> tag with the game name.
17. Add a <style> tag that centres the canvas and sets page background.
18. DO NOT use any deprecated Phaser methods.
19. Make the game actually fun — smooth controls, fair difficulty, clear feedback.
20. All game logic must work correctly — test every code path mentally.

Write the complete HTML file now:
"""


def _detect_game_type(game_design: str) -> str:
    """Detect game type from design document to inject relevant code example."""
    design_lower = game_design.lower()

    if any(word in design_lower for word in ["chess", "checkers", "board game", "turn-based"]):
        return "chess"
    if any(word in design_lower for word in ["platformer", "platform", "jump and run"]):
        return "platformer"
    if any(word in design_lower for word in ["snake"]):
        return "snake"
    if any(word in design_lower for word in ["runner", "endless run", "dino", "flappy", "dodge"]):
        return "runner"
    if any(word in design_lower for word in ["puzzle", "match", "tetris", "grid"]):
        return "puzzle"

    return ""


def run(
    game_design: str = None,
    pseudocode: str = None,
    draw_manifest: str = None,
    retry_feedback: str = None,
) -> str:
    if game_design is None:
        with open("output/game_design.md", "r", encoding="utf-8") as f:
            game_design = f.read()

    if pseudocode is None:
        with open("output/pseudocode.md", "r", encoding="utf-8") as f:
            pseudocode = f.read()

    if draw_manifest is None:
        manifest_path = "output/draw_manifest.md"
        if os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                draw_manifest = f.read()
        else:
            draw_manifest = "(No draw manifest available)"

    # Detect game type and inject relevant working example (Fix #2)
    game_type = _detect_game_type(game_design)
    game_example = GAME_EXAMPLES.get(game_type, "")
    if game_example:
        game_example = f"--- WORKING CODE EXAMPLE FOR {game_type.upper()} ---\nUse this as a reference pattern. Adapt it to the specific game design above.\n{game_example}"

    prompt = PROMPT_TEMPLATE.format(
        game_design=game_design,
        pseudocode=pseudocode,
        draw_manifest=draw_manifest,
        phaser_api_reference=PHASER_API_REFERENCE,
        game_example=game_example,
    )

    if retry_feedback:
        prompt += f"\n\n--- PREVIOUS ATTEMPT FAILED. FIX THESE ERRORS ---\n{retry_feedback}\n\nWrite the corrected complete HTML file now:"

    print("[Coding Agent] Generating Phaser 3 game code...")

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            safety_settings=SAFETY,
            thinking_config=types.ThinkingConfig(thinking_budget=24576),  # Flash max thinking budget
        ),
    )

    code = response.text.strip()

    # Strip markdown code fences if the model adds them despite instructions
    if code.startswith("```"):
        lines = code.split("\n")
        code = "\n".join(lines[1:])
    if code.endswith("```"):
        code = code[:-3].strip()

    os.makedirs("build/web", exist_ok=True)
    with open("build/web/game.html", "w", encoding="utf-8") as f:
        f.write(code)

    print("[Coding Agent] Done. Written to build/web/game.html")
    return code


if __name__ == "__main__":
    run()