// game.js
const config = {
    type: Phaser.AUTO,
    width: 1024,
    height: 768,
    parent: 'game-container',
    physics: { default: 'arcade' },
    scene: { preload, create, update }
};
const game = new Phaser.Game(config);

let buildingsGroup;
let heroesGroup;
let textPool = [];

function preload() {
    // background + building images depuis phaser labs (assets libres)
    this.load.image('sky', 'https://labs.phaser.io/assets/skies/sky4.png');
    this.load.image('Townhall', 'https://labs.phaser.io/assets/sprites/castle.png');
    this.load.image('Barracks', 'https://labs.phaser.io/assets/sprites/house.png');
    this.load.image('GoldMine', 'https://labs.phaser.io/assets/sprites/gold.png');
    this.load.image('ElixirCollector', 'https://labs.phaser.io/assets/sprites/purple_ball.png');
    this.load.image('Walls', 'https://labs.phaser.io/assets/sprites/block.png');
}

function create() {
    const scene = this;
    scene.add.image(512, 384, 'sky').setDisplaySize(1024, 768);

    buildingsGroup = scene.add.group();
    heroesGroup = scene.add.group();

    // créer textures dynamiques pour factions (cercles colorés) - pas besoin d'assets externes
    const factionColors = {
        "Gangs": 0xff3333,
        "Militaires": 0x33ff33,
        "Cyborgs": 0x33ffff,
        "AnimauxMod": 0xffff33,
        "Aliens": 0xaa33ff,
        "Orques": 0xff9933
    };

    Object.keys(factionColors).forEach(key => {
        const gfx = scene.make.graphics({ x: 0, y: 0, add: false });
        gfx.fillStyle(factionColors[key], 1);
        gfx.fillCircle(32, 32, 28);
        gfx.fillStyle(0x000000, 0.15);
        gfx.fillCircle(42, 22, 8);
        gfx.generateTexture(`hero_${key}`, 64, 64);
        gfx.destroy();
    });

    window.updateGameScene = (village) => {
        updateSceneFromVillage(scene, village);
    };
}

function update() {
    // pas d'animation continue complexe pour l'instant
}

function clearGroup(g) {
    g.getChildren().forEach(it => {
        if (it && it.destroy) it.destroy();
    });
}

function updateSceneFromVillage(scene, village) {
    clearGroup(buildingsGroup);
    clearGroup(heroesGroup);

    // bâtiments
    if (village.buildings) {
        village.buildings.forEach(b => {
            const img = scene.add.image(b.x, b.y, b.name).setScale(0.7);
            const lvl = scene.add.text(b.x - 30, b.y + 40, `Lv ${b.level}`, { fontSize: '14px', color: '#fff' });
            buildingsGroup.add(img);
            buildingsGroup.add(lvl);
            // si bâtiment en construction, montre un timer au-dessus
            if (b.building_until) {
                const remaining = Math.max(0, Math.round(b.building_until - Date.now() / 1000));
                const t = scene.add.text(b.x - 30, b.y - 60, `Construction: ${remaining}s`, { fontSize: '12px', color: '#ff0' });
                buildingsGroup.add(t);
            }
        });
    }

    // file de construction (global)
    if (village.build_queue && village.build_queue.length) {
        village.build_queue.forEach((q, i) => {
            const x = 900;
            const y = 40 + i * 28;
            const finish = new Date((q.finish_at || q.finishAt) * 1000);
            const s = scene.add.text(x, y, `${q.name} -> ${finish.toLocaleTimeString()}`, { fontSize: '12px', color: '#fff' });
            buildingsGroup.add(s);
        });
    }

    // héros : sprites dynamiques + label
    if (village.heroes) {
        village.heroes.forEach((h, idx) => {
            const key = `hero_${h.faction}`;
            // some heroes might be off-canvas; clamp
            const x = Phaser.Math.Clamp(h.x || (100 + idx * 60), 40, 980);
            const y = Phaser.Math.Clamp(h.y || 650, 40, 720);
            const spr = scene.add.image(x, y, key).setScale(0.9);
            const name = scene.add.text(x - 30, y + 30, `${h.name} (${h.level})`, { fontSize: '12px', color: '#fff' });
            heroesGroup.add(spr);
            heroesGroup.add(name);
        });
    }
}
