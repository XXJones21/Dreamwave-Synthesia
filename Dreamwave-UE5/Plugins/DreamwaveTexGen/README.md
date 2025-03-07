# Dreamwave Texture Generator Plugin for Unreal Engine 5

This plugin allows you to generate AI-powered textures directly within Unreal Engine using ComfyUI.

## Prerequisites

- Unreal Engine 5.5.3 or later
- Python 3.10+ (included with Unreal Engine)
- ComfyUI running on your local machine or a remote server

## Installation

1. Copy the `DreamwaveTexGen` folder to your Unreal Engine project's `Plugins` directory
2. Start Unreal Engine and enable the plugin in Edit > Plugins > AI > Dreamwave Texture Generator
3. Restart the Unreal Editor when prompted

## Usage

1. After restarting Unreal Engine, you'll find a new "Dreamwave" menu in the main toolbar
2. Click on Dreamwave > Open Texture Generator to open the texture generation UI
3. Enter your prompt and adjust settings as needed
4. Click "Generate Texture" to create a new texture
5. The generated texture will be automatically imported into your project's Content/DreamwaveTextures folder

## Configuration

You can configure the plugin settings in Project Settings > Plugins > Dreamwave Texture Generator:

- ComfyUI Server URL: The URL where ComfyUI is running (default: http://127.0.0.1:8188)
- Workflow File Path: Path to a custom ComfyUI workflow file (optional)
- Output Directory: Custom directory for saving generated textures
- Style Presets: You can modify the default style presets in the settings

## Troubleshooting

- Make sure ComfyUI is running and accessible at the configured URL
- If the plugin fails to load, check that Python scripting is enabled in your project
- For any texture generation errors, check the Output Log for detailed error messages

## License

Copyright © 2024 Dreamwave Synthesia. All rights reserved. 