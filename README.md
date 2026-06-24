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

# Anime Cloth Fold Generator Add-on (Blender 5.1.2)

This repository also contains a separate Blender add-on: `anime_cloth_folds.py`.

## What it does

- Creates stylized procedural cloth-fold displacement for anime character clothing.
- Lets you draw where folds appear using a **Weight Paint** vertex group named `Cloth Folds Mask`.
- Provides a non-destructive **Preview Cloth Folds** modifier workflow.
- Provides **Apply Cloth Folds** to bake the preview into the mesh.
- Writes a float point mesh attribute, `cloth_folds` by default, from the painted mask so materials can give folds a different texture or shader treatment.

## Install

1. Open Blender 5.1.2.
2. Go to **Edit → Preferences → Add-ons → Install...**
3. Pick `anime_cloth_folds.py`.
4. Enable **Anime Cloth Fold Generator**.

## Use

1. Select a mesh clothing object.
2. Open **3D View → Sidebar (N) → Cloth Folds → Anime Cloth Folds**.
3. Click **Create / Select Fold Paint Mask** and paint white where folds should appear.
4. Tune fold strength, spacing, contrast, sharpness, and pattern.
5. Click **Preview Cloth Folds** for a live, removable modifier.
6. Click **Create / Refresh Fold Attribute** if you only need the texture-selection attribute, or **Apply Cloth Folds** to bake the geometry and keep the attribute.

## Notes

- The add-on uses Blender's built-in Displace modifier and procedural textures, so the preview stays editable until applied.
- The `cloth_folds` attribute is a point-domain float attribute copied from the `Cloth Folds Mask` weights.
- In materials, use Blender's Attribute node with the same attribute name to target fold-specific colors, roughness, normals, or texture blends.
