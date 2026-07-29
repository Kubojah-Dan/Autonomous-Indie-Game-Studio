"""Pre-forged demo game 'Neon Runner' — seeded on first backend boot."""
from __future__ import annotations

from typing import Dict

DEMO_ID = "neon-runner"
DEMO_IDEA = "A cyberpunk endless runner where you outrun the debt collector across neon rooftops"

NEON_RUNNER_HTML = """<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='utf-8'/>
<title>NEON RUNNER :: QuantumForge</title>
<script src='https://cdn.jsdelivr.net/npm/phaser@3.70.0/dist/phaser.min.js'></script>
<style>
  html,body{margin:0;background:#0A0A0F;color:#00FF41;font-family:'Courier New',monospace;overflow:hidden}
  #tag{position:fixed;top:8px;left:12px;font-size:12px;letter-spacing:2px;color:#00F0FF;text-shadow:0 0 6px #00F0FF}
</style>
</head>
<body>
<div id='tag'>NEON RUNNER :: QUANTUMFORGE PROTOTYPE v1.0</div>
<script>
class Main extends Phaser.Scene {
  constructor(){ super('main'); }
  create(){
    this.cameras.main.setBackgroundColor('#0A0A0F');
    for(let i=0;i<24;i++){
      this.add.rectangle(Phaser.Math.Between(0,800), Phaser.Math.Between(0,400), 2, 2, 0x00F0FF, 0.6);
    }
    // ground
    this.ground = this.add.rectangle(400, 560, 800, 40, 0x00FF41, 0.15);
    this.physics.add.existing(this.ground, true);

    // player
    this.player = this.add.rectangle(120, 480, 26, 40, 0x00FF41);
    this.physics.add.existing(this.player);
    this.player.body.setBounce(0.1);
    this.player.body.setCollideWorldBounds(true);
    this.physics.add.collider(this.player, this.ground);

    // enemies group
    this.enemies = this.physics.add.group();
    this.spawnTimer = 0;

    // input
    this.cursors = this.input.keyboard.createCursorKeys();
    this.spaceKey = this.input.keyboard.addKey(Phaser.Input.Keyboard.KeyCodes.SPACE);

    // hud
    this.score = 0;
    this.scoreText = this.add.text(20, 20, 'SCORE 0', {fontFamily:'monospace', fontSize:'20px', color:'#00FF41'});
    this.hintText = this.add.text(400, 30, 'SPACE/UP to JUMP', {fontFamily:'monospace', fontSize:'14px', color:'#00F0FF'}).setOrigin(0.5);
    this.gameOver = false;
  }
  update(time, delta){
    if (this.gameOver){
      if (Phaser.Input.Keyboard.JustDown(this.spaceKey)) this.scene.restart();
      return;
    }
    // jump
    if ((this.cursors.up.isDown || this.spaceKey.isDown) && this.player.body.touching.down) {
      this.player.body.setVelocityY(-420);
    }
    // spawn debt collector obstacles
    this.spawnTimer += delta;
    if (this.spawnTimer > 1200) {
      this.spawnTimer = 0;
      const e = this.add.rectangle(820, 520, 22, 36, 0xFF00E5);
      this.physics.add.existing(e);
      e.body.setVelocityX(-260 - Math.min(200, this.score/2));
      e.body.setAllowGravity(false);
      this.enemies.add(e);
      this.physics.add.overlap(this.player, e, () => this.end());
    }
    // score
    this.score += delta * 0.03;
    this.scoreText.setText('SCORE ' + Math.floor(this.score));
    // cleanup off-screen
    this.enemies.getChildren().forEach(e => { if (e.x < -40) e.destroy(); });
  }
  end(){
    this.gameOver = true;
    this.add.rectangle(400,300,520,180,0x0A0A0F).setStrokeStyle(2,0xFF00E5);
    this.add.text(400,270,'SYSTEM :: FAILURE',{fontFamily:'monospace',fontSize:'26px',color:'#FF00E5'}).setOrigin(0.5);
    this.add.text(400,310,'FINAL SCORE ' + Math.floor(this.score),{fontFamily:'monospace',fontSize:'20px',color:'#00FF41'}).setOrigin(0.5);
    this.add.text(400,345,'[ SPACE TO REBOOT ]',{fontFamily:'monospace',fontSize:'16px',color:'#00F0FF'}).setOrigin(0.5);
  }
}
new Phaser.Game({
  type: Phaser.AUTO, width: 800, height: 600, parent: document.body,
  backgroundColor: '#0A0A0F',
  physics: { default: 'arcade', arcade: { gravity: { y: 900 } } },
  scene: Main,
});
</script>
</body>
</html>
"""


def demo_artifacts() -> Dict[str, str]:
    return {
        "plan": (
            "1. Expand pitch into cyberpunk endless-runner concept.\n"
            "2. Scout Canabalt / Bit.Trip Runner / Neon Abyss for reference.\n"
            "3. Lock a one-button jump loop with rising difficulty.\n"
            "4. Draft neon-noir story beats.\n"
            "5. Ship a Phaser 3 prototype with color-block art."
        ),
        "concept": (
            "TITLE: NEON RUNNER\n\n"
            "ELEVATOR PITCH: Outrun the debt collector across neon rooftops for as long as your credit rating holds.\n\n"
            "GENRE: Cyberpunk one-button endless runner.\n"
            "AUDIENCE: Arcade fans, coffee-break gamers, cyberpunk aesthetes.\n"
            "CORE FANTASY: Fast, defiant, permanent-underclass sprint through a city that wants you dead.\n"
            "HOOK: Every collector you dodge raises the tempo; the city glitches faster the longer you survive."
        ),
        "references": (
            "- Canabalt :: Defined one-button rooftop running; teaches procedural obstacle rhythm.\n"
            "- Bit.Trip Runner :: Music-driven pacing, punchy failure moments.\n"
            "- Neon Abyss :: Cyberpunk color palette and gonzo enemy design."
        ),
        "mechanics": (
            "CORE LOOP:\n"
            "- Auto-run right at increasing speed.\n"
            "- Time jumps to clear debt collectors.\n"
            "- Miss one and the run ends.\n\n"
            "CONTROLS: SPACE / UP ARROW = jump.\n"
            "WIN: Beat your high score.\n"
            "LOSE: Any collector collision.\n\n"
            "MECHANICS:\n"
            "1. Adaptive spawn rate — collectors accelerate with score.\n"
            "2. Coyote-time jump — 80ms grace after leaving a ledge.\n"
            "3. Neon streaks — visual feedback for speed tier.\n"
            "4. Glitch pulse — brief slow-mo on near-miss.\n"
            "5. Reboot loop — instant restart on SPACE."
        ),
        "story": (
            "The city sold your debt to a syndicate that prints faster than legs. You wake on a rooftop with a "
            "billboard laughing your name in pink; the only direction out is forward.\n\n"
            "Somewhere down there a woman named MIRA is unlocking exits for runners who make it far enough.\n\n"
            "CHARACTERS:\n"
            "- KIT (Player): Ex-courier, one lung of chrome, allergic to standing still.\n"
            "- MIRA: Rogue accountant leaking rooftop maps to the underclass."
        ),
        "sprite_prompts": (
            "PROMPT_PLAYER: Pixel-art side-view runner in a magenta hoodie, chrome sneakers, glowing green cybernetic arm, transparent bg.\n"
            "PROMPT_ENEMY: Pixel-art hovering debt-collector drone, chrome + hot pink, red scanner eye, 32x32 sprite sheet.\n"
            "PROMPT_TILESET: Rooftop tileset, neon-lit AC units, holographic billboards, wet concrete, 16x16 tiles.\n"
            "PROMPT_COVER: Cyberpunk key art of a magenta-hooded runner leaping across neon rooftops, rain, chromatic aberration."
        ),
        "levels": (
            "LEVEL 1 :: STARTER STRIP\n"
            "####################\n"
            "P..................X\n"
            "....................\n"
            "....E.......E.......\n"
            "####################\n\n"
            "LEVEL 2 :: BILLBOARD ROW\n"
            "####################\n"
            "P.....##......##...X\n"
            "..E.....E......E....\n"
            "####################\n\n"
            "LEVEL 3 :: FIREWALL RUN\n"
            "####################\n"
            "P.##..E..##..E..##.X\n"
            "..E....E....E.......\n"
            "####################"
        ),
        "code": NEON_RUNNER_HTML,
        "qa_report": (
            "FUN_SCORE: 8/10\n"
            "BUGS: none critical.\n"
            "PATCHES: Consider adding a small landing-particle burst; the jump feels punchy already.\n"
            "VERDICT: PASS"
        ),
        "balance": (
            "PARAM              | DEFAULT | EFFECT\n"
            "-------------------+---------+-----------------------------------\n"
            "spawn_rate_ms      | 1200    | Lower = harder, more collectors\n"
            "base_enemy_speed   | 260     | Base rightward drift of debt drone\n"
            "speed_score_scale  | 0.5     | Extra px/s per point of score\n"
            "jump_impulse       | 420     | Higher = floatier player\n"
            "gravity_y          | 900     | Higher = snappier fall"
        ),
    }
