# Hammer-Style Scene + UV Tools (Blender 5.1.1)

This add-on gives Blender a **Hammer-like workflow** so you can build scenes quickly and texture them with tiled UVs without stretching.

## Included tools

- **Apply Hammer Grid**: configures snapping/grid for level-style blockout.
- **Brush Builder**: quickly spawn cube/cylinder/plane primitives from dimensions.
- **Room Shell**: generate a simple enclosed room shell with wall thickness.
- **Scene Rig**: one-click camera + target + sun light setup around the 3D cursor.
- **Hammer UV Tiling**: dominant-axis per-face UV projection with tile scale, offsets, rotation, and world-space lock.

## Install

1. Open Blender **5.1.1**.
2. Go to **Edit → Preferences → Add-ons → Install...**
3. Select `hammer_uv_tools.py`.
4. Enable **Hammer-Style Scene + UV Tools**.

## Use

1. Open **3D View → Sidebar (N) → Hammer**.
2. Use **Scene/Grid** first to enable snapping workflow.
3. Use **Brush Builder** and **Room Shell** to block out your scene.
4. Use **Scene Rig** to create quick lighting/camera for previews/animation setup.
5. In Edit Mode, use **Hammer UV Tiling** on selected faces to keep textures tiled and unstretched.

## Notes

- Designed for users familiar with Valve Hammer workflows.
- World-space UV lock keeps texture scale consistent across multiple meshes.
