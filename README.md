# Hammer-Style UV Tiling Add-on (Blender 5.1.1)

This repository contains a Blender add-on: `hammer_uv_tools.py`.

## What it does

- Projects selected mesh faces with a **Hammer-like planar mapping** workflow.
- Keeps textures **tiled in world/object units** instead of stretching across arbitrary face sizes.
- Lets you tweak:
  - Tile size (U/V)
  - Offset (U/V)
  - Rotation
  - World-space lock (on by default)

## Install

1. Open Blender 5.1.1.
2. Go to **Edit → Preferences → Add-ons → Install...**
3. Pick `hammer_uv_tools.py`.
4. Enable **Hammer-Style UV Tiling**.

## Use

1. Select a mesh object and enter **Edit Mode**.
2. Select faces.
3. Open **3D View → Sidebar (N) → UV → Hammer UV Tiling**.
4. Set tile size and other controls.
5. Click **Hammer Tiled Project**.

## Notes

- This tool picks projection axes per face using the face normal's dominant axis.
- That behavior mimics classic "face-based planar" texturing and prevents common UV stretching.
