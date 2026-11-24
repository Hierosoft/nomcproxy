# Player help: Minecraft 1.5.2, Hexxit, and Blightfall

Short notes on differences from modern Minecraft that affect everyday play. <br>
For full details follow the wiki links. This page is not a complete guide.

## Build height

In Minecraft 1.5.2 the world is still 256 blocks tall (Y=0 to Y=255). <br>
You can place blocks up to Y=255. Natural terrain generation mostly stays well below that. <br>
(Modern Minecraft raised the limit further and added negative Y levels.)

The height limit was raised from 128 to 256 in 1.2.1 with the Anvil world format and remained 256 in 1.5.2. <br>
See [Java Edition 1.2.1 – Minecraft Wiki](https://minecraft.wiki/w/Java_Edition_1.2.1) for the height change.

## Mining depths

Approximate best levels for branch mining in vanilla 1.5.2 (Y = the level under your feet in a 2-high tunnel). <br>
Ore distribution is essentially the same as in 1.2.5:

| Ore | Best Y range | Notes |
|-----|--------------|-------|
| Diamond | 10–16 | Most common near Y=12. |
| Redstone | 10–16 | Same general band as diamond. |
| Gold | 1–32 | Even distribution in this range. |
| Iron | 1–64 | More common higher up. |
| Coal | 1–128 | Abundant at almost any depth. |
| Lapis | ~16 | Centered around Y=16. |

Lava lakes become common below ~Y=10. <br>
Always check the F3 debug screen for your exact Y coordinate.

Ore distribution in this era is the same as 1.2.5; the modern [Ore](https://minecraft.wiki/w/Ore) page shows current generation and does not apply.

## Fences and gates

### Wooden fence
Craft with 6 sticks (3×2 vertical). Connects to other wooden fences and fence gates. <br>
Mobs cannot jump over a single fence. Collision box is 1.5 blocks tall.

### Nether brick fence
Craft with 6 nether bricks. Fireproof and stronger. Generates in nether fortresses. <br>
Does not visually connect directly to wooden fences (use a gate between them).

### Fence gate
Craft with 4 sticks + 2 wooden planks. Opens by right-click or redstone. <br>
Connects to both wooden and nether brick fences.

See [Fence – Minecraft Wiki](https://minecraft.wiki/w/Fence) and [Fence Gate – Minecraft Wiki](https://minecraft.wiki/w/Fence_Gate).

## Other notable vanilla differences

- Stairs do not automatically form modern-style corners.
- Wood types are still limited (oak, spruce, birch, jungle).
- No shields, no off-hand, no later sprint/jump or combat changes.
- Redstone received the 1.5 “Redstone Update” (hoppers, droppers, comparators, etc.).
- Beds set spawn point; Essentials may also create a special named “bed” home (see [player-commands.md](player-commands.md)).

Full changelog and feature history: [Java Edition 1.5 – Minecraft Wiki](https://minecraft.wiki/w/Java_Edition_1.5).

## Hexxit

Hexxit is a Minecraft 1.5.2 adventure/RPG-focused modpack (Technic). <br>
It emphasizes exploration, dungeons, towers, and dangerous mobs over pure tech.

### Key differences from vanilla 1.5.2

- Many extra biomes, structures, and hostile mobs (including Infernal Mobs-style enhanced enemies).
- Extra dimensions and portals (notably Twilight Forest).
- Custom gear, weapons, and armor sets (Hexxit Gear, Legend Gear, etc.).
- Mining is still done at classic Y levels, but new ores and cave features appear.

Start here: [Hexxit – Technic Platform](https://www.technicpack.net/modpack/hexxit.552552). <br>
Mod list and further reading are on the same page and on the [Hexxit FTB Wiki](https://ftb.fandom.com/wiki/Hexxit).

## Blightfall

Blightfall is a story-driven Technic modpack and adventure map centered on surviving a planet covered in Thaumcraft taint. <br>
(In this project’s documentation it is grouped with the 1.5.2-era stack; the classic public pack is 1.7.10.)

### Key differences from vanilla

- The surface is largely uninhabitable purple taint; you begin in a bioshelter / colony ship (the Jaded).
- Progression is guided by Hardcore Questing Mode and Custom NPCs.
- Heavy focus on Thaumcraft (taint, research, magic) plus tech mods (Thermal Expansion, Tinkers’ Construct, Applied Energistics, etc.).
- Ores and resources are more biome-specific and scarce; exploration and quests matter more than pure branch mining.

Start here: [Blightfall – Technic Platform](https://www.technicpack.net/modpack/blightfall.592618). <br>
Getting-started and quest notes: [Getting Started – Blightfall Wikia](https://blightfall.fandom.com/wiki/Getting_Started).

For server-specific commands (homes, locks, Towny, etc.) see [player-commands.md](player-commands.md).
