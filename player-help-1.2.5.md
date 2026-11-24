# Player help: Minecraft 1.2.5 and Tekkit Classic

Short notes on differences from modern Minecraft that affect everyday play. <br>
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
Craft with 6 sticks (3×2 vertical). Connects to other fences and fence gates. <br>
Mobs cannot jump over a single fence.

### Nether brick fence
Craft with 6 nether bricks. Fireproof and stronger. Generates in nether fortresses.

### Fence gate
Craft with 4 sticks + 2 wooden planks. Opens by right-click or redstone. <br>
Connects to both wooden and nether brick fences.

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

### Fences and gates

#### Iron Fence (IndustrialCraft²)
More than a decorative fence. <br>
- Stack them to make a pole. Hold crouch to slide down quickly (no fall damage).
- With a Magnetizer and Magnetic Boots (Iron/Gold/Nano/Quantum), standing near a powered Iron Fence pole lifts you upward.

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

Recipe and full list: [Talisman of Repair – Tekkit Classic Wiki](https://tekkitclassic.fandom.com/wiki/Talisman_of_Repair).

### Further reading

- Main pack wiki: [Tekkit Classic Wiki](https://tekkitclassic.fandom.com/wiki/Main_Page)
- Equivalent Exchange overview: [Equivalent Exchange – Tekkit Classic Wiki](https://tekkitclassic.fandom.com/wiki/Equivalent_Exchange)
- IndustrialCraft² and Railcraft have their own pages on the same wiki.

For server-specific commands (homes, locks, Towny, etc.) see [player-commands.md](player-commands.md).
