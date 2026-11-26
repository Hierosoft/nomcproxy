# Player help: Minecraft 1.2.5 and Tekkit Classic

Short notes on differences from modern Minecraft that affect everyday play. <br>
This is a version-specific supplement to the main [player-help.md](player-help.md). <br>
For full details follow the wiki links. This page is not a complete guide.

## Build height

In Minecraft 1.2.5 the world is 256 blocks tall (Y=0 to Y=255). <br>
You can place blocks up to Y=255. Natural terrain generation mostly stays well below that. <br>
(Modern Minecraft raised the limit further and added negative Y levels.)

The height limit was raised from 128 to 256 in 1.2.1 with the Anvil world format. <br>
See [Java Edition 1.2.1 – Minecraft Wiki](https://minecraft.wiki/w/Java_Edition_1.2.1) for that change.

## Mining depths

Approximate best levels for branch mining in vanilla 1.2.5 (Y = the level under your feet in a 2-high tunnel):

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

Ore distribution in this era is described in older references; the modern [Ore](https://minecraft.wiki/w/Ore) page shows current generation and does not apply.

## Fences and gates

### Wooden fence
6 sticks in two vertical columns. Connects to other fences and fence gates. <br>
Mobs cannot jump over a single fence.

| | | |
|---|---|---|
| | 🪵 | 🪵 |
| | 🪵 | 🪵 |
| | 🪵 | 🪵 |

### Nether brick fence
6 nether bricks. Fireproof and stronger. Generates in nether fortresses.

| | | |
|---|---|---|
| | 🧱 | 🧱 |
| | 🧱 | 🧱 |
| | 🧱 | 🧱 |

### Fence gate
4 sticks + 2 wooden planks. Opens by right-click or redstone. <br>
Connects to both wooden and nether brick fences.

| | | |
|---|---|---|
| | | |
| 🪵 | 🪵 | 🪵 |
| 🪵 | 🪵 | 🪵 |

**Emoji key (vanilla):** 🪵 Stick or Wooden Planks · 🧱 Nether Brick

See [Fence – Minecraft Wiki](https://minecraft.wiki/w/Fence) and [Fence Gate – Minecraft Wiki](https://minecraft.wiki/w/Fence_Gate).

## Other notable vanilla differences

- Stairs do not automatically form corners the way modern stairs do.
- Fewer wood types (oak, spruce, birch, jungle only).
- No shields, no off-hand, no sprint-jump changes that came later.
- Beds set spawn point; Essentials may also create a special named “bed” home (see [player-commands.md](player-commands.md)).

Full changelog and feature history: [Java Edition 1.2.5 – Minecraft Wiki](https://minecraft.wiki/w/Java_Edition_1.2.5).

## Tekkit Classic

Tekkit Classic is the Minecraft 1.2.5 modpack that adds IndustrialCraft, BuildCraft, Equivalent Exchange, Railcraft, and others. <br>
Many extra blocks and items exist only in the pack.

### Minimap (Rei’s Minimap)

Tekkit Classic includes Rei’s Minimap. <br>
Press **'** (apostrophe) for the large map. <br>
Other keys (menu, waypoints, etc.) can be changed in the minimap options.

See [Rei’s Minimap – Tekkit Classic Wiki](https://tekkitclassic.fandom.com/wiki/Rei%27s_Minimap).

### Fences and gates

#### Iron Fence (IndustrialCraft²)
More than a decorative fence. <br>
- Stack them to make a pole. Hold crouch to slide down quickly (no fall damage).
- With a Magnetizer and Magnetic Boots (Iron/Gold/Nano/Quantum), standing near a powered Iron Fence pole lifts you upward.

6 Refined Iron (top two rows):

| | | |
|---|---|---|
| 🔩 | 🔩 | 🔩 |
| 🔩 | 🔩 | 🔩 |
| | | |

Recipe and details: [Iron Fence – Tekkit Classic Wiki](https://tekkitclassic.fandom.com/wiki/Iron_Fence).

#### Gated Track (Railcraft)
A minecart rail that acts like a fence gate (opens/closes by hand or redstone). <br>
Crafted with standard rails + fence gates + wooden railbed. <br>
There is also a one-way version that boosts carts through.

See [Gated Track – Tekkit Classic Wiki](https://tekkitclassic.fandom.com/wiki/Gated_Track).

### Repair Pendant (Talisman of Repair)

An Equivalent Exchange item that repairs tools and armor before they break. <br>
- Works from anywhere in your inventory (does not need to be on the hotbar).
- Consumes one matching Covalence Dust per repair:
  - Low → wood/stone tools, leather armor, etc.
  - Medium → iron/gold/bronze/etc.
  - High → diamond tools and armor.
- Placing the Talisman on a DM Pedestal or inside an Alchemical Chest with the tools repairs them without consuming dust (slowly).

| | | |
|---|---|---|
| 🟢 | 🧵 | 🔴 |
| 🔵 | 📄 | 🔵 |
| 🔴 | 🧵 | 🟢 |

**Emoji key (EE):** 🟢 Low Covalence Dust · 🔵 Medium Covalence Dust · 🔴 High Covalence Dust · 🧵 String · 📄 Paper

Recipe and full list: [Talisman of Repair – Tekkit Classic Wiki](https://tekkitclassic.fandom.com/wiki/Talisman_of_Repair).

### Common crafting recipes (Tekkit Classic)

These are early IndustrialCraft² and Equivalent Exchange items that do not exist in vanilla 1.2.5. <br>
Refined Iron is made by smelting a normal Iron Ingot again. <br>
Always use a Wrench to pick up machines that contain a Machine Block.

#### Machine Block
8 Refined Iron in a ring:

| | | |
|---|---|---|
| 🔩 | 🔩 | 🔩 |
| 🔩 | | 🔩 |
| 🔩 | 🔩 | 🔩 |

#### RE Battery
(First make Copper Cable from 3 Copper Ingots in a row, then Insulated Copper Cable by surrounding it with Rubber.)

| | | |
|---|---|---|
| | | |
| 🪙 | 🔌 | 🪙 |
| | 🔴 | |

#### Generator
(Basic coal-powered EU source.)

| | | |
|---|---|---|
| | 🔋 | |
| | ⬛ | |
| | 🔥 | |

#### BatBox
(Stores up to 40,000 EU. Output face is the side with the orange dot; change it with a Wrench.)

| | | |
|---|---|---|
| 🪵 | 🔌 | 🪵 |
| 🔋 | 🔋 | 🔋 |
| 🪵 | 🪵 | 🪵 |

#### Macerator
(Doubles most ores into dust that can be smelted into 2 ingots.)

| | | |
|---|---|---|
| 🪨 | 🪨 | 🪨 |
| 🪨 | ⬛ | 🪨 |
| | 🔌 | |

#### Philosopher’s Stone (Equivalent Exchange)
(Used to transmute blocks and craft higher EE fuels. Returned after most crafts.)

| | | |
|---|---|---|
| ✨ | 🔴 | ✨ |
| 🔴 | 💎 | 🔴 |
| ✨ | 🔴 | ✨ |

**Emoji key:** 🔩 Refined Iron · 🪙 Tin · 🔌 Insulated Copper Cable / Electronic Circuit · 🔴 Redstone · 🔋 RE Battery · ⬛ Machine Block · 🔥 Furnace · 🪵 Wooden Planks · 🪨 Flint or Cobblestone · ✨ Glowstone Dust · 💎 Diamond

Full recipes and more machines: [Tekkit Classic Wiki](https://tekkitclassic.fandom.com/wiki/Main_Page) (search for the item).

### Further reading

- Main pack wiki: [Tekkit Classic Wiki](https://tekkitclassic.fandom.com/wiki/Main_Page)
- Equivalent Exchange overview: [Equivalent Exchange – Tekkit Classic Wiki](https://tekkitclassic.fandom.com/wiki/Equivalent_Exchange)
- IndustrialCraft² and Railcraft have their own pages on the same wiki.

For server-specific commands (homes, locks, Towny, etc.) see [player-commands.md](player-commands.md).
