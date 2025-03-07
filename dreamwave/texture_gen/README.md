# 🌀 Dreamwave Texture Generation

A Python-based tool for generating textures using AI models via ComfyUI, with Unreal Engine 5 integration.

## 📚 Overview

This module is part of the Dreamwave Synthesia project and provides:

1. A Python API for generating textures using the FLUX.1-schnell model via ComfyUI
2. An Unreal Engine 5 plugin for technical artists to generate textures directly in-editor
3. Streamlined workflow from text prompt to usable UE5 texture asset

## 🚀 Quick Start

### Python Setup

1. Install required dependencies:
```bash
pip install -r texture_gen/requirements.txt
```

2. Test the ComfyUI bridge:
```bash
cd dreamwave
python -m texture_gen.test_bridge --prompt "vaporwave grid texture with neon pink glow"
```

### Unreal Engine Plugin Setup

1. Copy the `UnrealPlugin/DreamwaveTexGen` directory to your Unreal Engine project's `Plugins` directory
2. Copy the `dreamwave` directory to your Unreal Engine project's root directory
3. Start your Unreal Engine project and enable the "Dreamwave Texture Generator" plugin
4. Configure the plugin settings in Project Settings > Plugins > Dreamwave Texture Generator

## 💻 Usage

### From Python

```python
from dreamwave.texture_gen.comfy_bridge import ComfyBridge

# Initialize the bridge
bridge = ComfyBridge(server_address="http://localhost:8188")

# Generate a texture
texture_path = bridge.generate_texture(
    prompt="Cyberpunk metal surface with holographic reflections",
    output_dir="./output",
    workflow_path="path/to/FluxSchnell_workflow.json"
)

print(f"Generated texture at: {texture_path}")
```

### From Unreal Engine Editor (Python)

```python
import unreal

# Import the Dreamwave API
import dreamwave_texgen_api

# Generate and import a texture
texture_asset = dreamwave_texgen_api.generate_and_import(
    prompt="Retro neon grid with synthwave sunset",
    style_presets=["vaporwave", "80s"],
    asset_name="T_RetroNeonGrid",
    asset_path="/Game/Textures/Synthwave"
)

# Apply to a selected material in the editor
if texture_asset:
    selected_assets = unreal.EditorUtilityLibrary.get_selected_assets()
    for asset in selected_assets:
        if isinstance(asset, unreal.Material) or isinstance(asset, unreal.MaterialInstanceConstant):
            # Apply as base color
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                asset, "BaseColor", texture_asset
            )
            unreal.log(f"Applied texture to {asset.get_name()}")
```

### From Unreal Engine UI

1. Open the Dreamwave Texture Generator from the toolbar or Tools menu
2. Enter a text prompt describing the texture you want to generate
3. Select style presets (optional)
4. Click "Generate"
5. Preview the generated texture
6. Click "Import to UE" to import the texture
7. Apply the texture to your materials

## ⚙️ ComfyUI Setup

The texture generation relies on a properly configured ComfyUI server with the FLUX.1-schnell model. 

1. Start the ComfyUI server:
```bash
cd ComfyUI/ComfyUI_windows_portable
python main.py
```

2. Load the FluxSchnell_workflow.json in the ComfyUI interface to verify it works
3. Ensure the server is accessible at http://localhost:8188 (default)

## 🛠️ Technical Details

### Architecture

```
       +---------------------+
       |   Unreal Engine 5   |
       |                     |
       |  +--------------+   |          +------------------+
       |  | UE5 Plugin   |   |  HTTP/   |                  |
       |  |              |<------------->   ComfyUI Server |
       |  | Python API   |   | WebSocket|                  |
       |  +--------------+   |          +------------------+
       +---------------------+                |
                                             |
                                             v
                                      +--------------+
                                      |  FLUX Model  |
                                      +--------------+
```

### Key Components

1. **ComfyBridge**: Core Python class for communicating with ComfyUI
2. **DreamwaveTexGenAPI**: UE5-specific wrapper for the ComfyBridge
3. **Workflow JSON**: Configuration for ComfyUI defining the AI processing graph

## 🧪 Troubleshooting

### Common Issues

1. **WebSocket Connection Error**
   - Make sure ComfyUI server is running
   - Check that the server URL is correct in the plugin settings
   - Verify firewall settings allow connections

2. **Workflow Not Found**
   - Ensure the workflow path is set correctly in the plugin settings
   - Check that FLUX.1-schnell model is properly installed in ComfyUI

3. **Texture Import Failed**
   - Verify UE5 has write permissions to the specified output directory
   - Check UE5 Python console for detailed error messages

## 🔮 Next Steps

Future enhancements planned for the texture generation system:

1. Add batch generation for creating texture sets (diffuse, normal, roughness, etc.)
2. Implement material auto-creation from generated textures
3. Add node-based workflow editor within UE5
4. Support for tileable texture generation
5. Integration with material instances for real-time previewing 