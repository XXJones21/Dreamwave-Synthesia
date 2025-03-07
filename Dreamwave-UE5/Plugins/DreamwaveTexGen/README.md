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

After restarting Unreal Engine, you can access Dreamwave functionality in two ways:

### Main Menu

The plugin adds a new "Dreamwave" entry to the main menu with these options:
- **Texture Generator**: Opens the main texture generation UI
- **Launch ComfyUI Server**: Starts the ComfyUI backend server if it's not running
- **Check ComfyUI Status**: Checks if the ComfyUI server is available

### Toolbar Button

A "Dreamwave" button is added to the main toolbar for quick access to the Texture Generator.

### Using the Generator

1. Click on the Dreamwave button in the toolbar or use the main menu
2. Enter your prompt and adjust settings as needed
3. Click "Generate Texture" to create a new texture
4. The generated texture will be automatically imported into your project's Content/DreamwaveTextures folder

## Technical Details

The plugin uses the Unreal Engine extension system to add UI elements rather than direct toolbar manipulation. This ensures compatibility with different UE 5.5+ versions and follows best practices for editor customization.

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
- If UI elements don't appear, check the Output Log for menu registration errors

## License

Copyright © 2024 Dreamwave Synthesia. All rights reserved. 