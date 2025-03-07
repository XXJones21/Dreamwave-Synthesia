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
4. The plugin will automatically detect and help set up ComfyUI if needed

## ComfyUI Integration

The plugin now includes comprehensive ComfyUI integration features:

- **Automatic ComfyUI Detection**: The plugin automatically searches for ComfyUI installations in common locations
- **Dependency Management**: Missing Python packages (like PyTorch, YAML) are detected and installed automatically
- **Multiple Launch Methods**: Several fallback approaches ensure ComfyUI starts reliably on different systems
- **Diagnostic Logging**: Detailed log files help diagnose any issues with the ComfyUI server
- **Browser Integration**: Easily open the ComfyUI web interface directly from Unreal Engine

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

- **ComfyUI Server Issues**: The plugin now provides detailed diagnostics if the ComfyUI server fails to start. Check the log file in the plugin's Python/logs directory for specific error messages.
- **Missing Dependencies**: The plugin will automatically detect and offer to install required Python packages. If you prefer to install them manually, run: `python -m pip install torch torchvision pyyaml`.
- **Server Connection Errors**: If you get connection errors, check that no firewall is blocking port 8188 which ComfyUI uses by default.
- **Alternative Connection Method**: If automatic server detection fails, you can manually specify the ComfyUI server URL in the plugin settings.
- Make sure ComfyUI is running and accessible at the configured URL
- If the plugin fails to load, check that Python scripting is enabled in your project
- For any texture generation errors, check the Output Log for detailed error messages
- If UI elements don't appear, check the Output Log for menu registration errors

## License

Copyright © 2024 Dreamwave Synthesia. All rights reserved. 