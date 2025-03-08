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

## Known Issues and Fixes

### ComfyUI Server Management Issues

Recent updates have addressed several critical issues with how the plugin manages the ComfyUI server process:

#### 1. Server Shutdown Mechanism

**Issue**: Previously, the ComfyUI server did not properly shut down when Unreal Engine was closed, leaving orphaned Python processes running in the background. In some cases, this could even cause Unreal Engine to relaunch unexpectedly.

**Fix**: We've implemented multiple redundant shutdown methods:
- Process tracking with PID file storage for persistent identification
- Windows-specific commands to find and terminate orphaned processes
- Graceful termination with fallback to forced killing
- Batch file cleanup to prevent script-related issues

**Commands**:
- `dreamwave_command.shutdown_comfyui()` - Gracefully shut down the ComfyUI server
- `dreamwave_command.force_kill_comfyui()` - Forcefully terminate any ComfyUI processes (emergency use)

#### 2. Dependency Management

**Issue**: The plugin required additional Python packages like `psutil` and `websocket-client` which were not being properly managed.

**Fix**: 
- Made external dependencies optional with graceful fallbacks
- Added improved error handling and logging
- Enhanced diagnostics for dependency-related issues
- Provided alternative implementation paths when dependencies are missing

#### 3. Unreal Engine Integration

**Issue**: Process handling between Unreal Engine and the ComfyUI server was causing conflicts, including Python environment contamination and unexpected process behavior.

**Fix**:
- Isolated ComfyUI server processes from Unreal Engine's environment
- Used batch files with proper environment separation
- Implemented better process detection and cleanup
- Provided detailed logging for diagnostic purposes

### FluxSchnell Workflow Issues

**Issue**: The FluxSchnell workflow validation was failing with 404 errors because the API endpoints differed across ComfyUI versions.

**Fix**:
- Enhanced model validation to accommodate different API structures
- Added better error handling for missing models
- Implemented graceful fallbacks to standard workflows when requirements aren't met
- Improved user feedback during the validation process

### Current Limitations

- **WebSocket Module**: Real-time progress updates require the optional `websocket-client` Python package
- **psutil Module**: Some advanced process management features require the optional `psutil` Python package
- **Process Isolation**: The server runs as a separate process, which improves stability but makes direct management more complex
- **API Compatibility**: The plugin is designed for recent ComfyUI versions; older versions may have compatibility issues

If you encounter any other issues, please check the log files in the plugin's Python/logs directory for detailed diagnostic information.

### Installing Optional Dependencies

For the best experience, we recommend installing these optional Python packages:

#### WebSocket Client (for real-time progress updates)

The `websocket-client` package enables real-time progress feedback during texture generation. To install:

1. Find your Unreal Engine Python executable (typically in `Engine/Binaries/ThirdParty/Python3/Win64/python.exe`)
2. Open a command prompt as administrator and run:
   ```
   "C:/Path/To/UE/Engine/Binaries/ThirdParty/Python3/Win64/python.exe" -m pip install websocket-client
   ```
3. Alternatively, you can let the plugin attempt to install it automatically by running a texture generation

#### PSUtil (for enhanced process management)

The `psutil` package improves process management and server shutdown reliability. To install:

1. Using the same Python executable as above, run:
   ```
   "C:/Path/To/UE/Engine/Binaries/ThirdParty/Python3/Win64/python.exe" -m pip install psutil
   ```
2. This package significantly improves the reliability of server shutdown when Unreal Engine closes

Note: The plugin will function without these packages, but with reduced capabilities. Installation messages in the Output Log will guide you if dependencies are missing.

### UI Enhancements

The texture generator UI has been significantly improved for better usability and feedback:

#### Real-time Progress Tracking

The UI now provides real-time progress updates during texture generation when the WebSocket module is available:
- A progress dialog shows the current status of the generation process
- Detailed node execution information is displayed (current node, execution time)
- Error messages are shown directly in the progress dialog
- Generation IDs are tracked for reliable progress association

#### FluxSchnell Workflow Integration

A new option to use the faster FluxSchnell workflow has been added:
- Radio buttons in the window-based UI for selecting workflow type
- Dialog prompt in the simple UI asking if you want to use FluxSchnell
- Automatic validation of required FluxSchnell models with graceful fallback
- Specialized prompt construction for the FluxSchnell workflow

#### Negative Prompts Support

The UI now supports negative prompts for better control over texture generation:
- Specify features you want to avoid in the generated textures
- Passed directly to the workflow for both standard and FluxSchnell methods
- Properly formatted based on the selected workflow type

#### Compatibility Improvements

The UI is now more compatible with different Unreal Engine versions:
- Window-based approach for recent UE versions with Python Window Library
- Dialog-based fallback for older versions or when libraries are unavailable
- Consistent functionality across both interface modes
- Enhanced error handling with informative messages

## Python Console Commands

For advanced users and developers, the plugin provides several Python commands that can be executed directly in Unreal Engine's Output Log console or Python Editor:

### Basic Commands

```python
# Open the Texture Generator UI
dreamwave_command.run_dreamwave()

# Check if the ComfyUI server is running
dreamwave_command.check_comfyui()

# Launch the ComfyUI server if it's not running
dreamwave_command.launch_comfyui()

# Shut down the ComfyUI server gracefully
dreamwave_command.shutdown_comfyui()

# Force kill all ComfyUI processes (emergency use only)
dreamwave_command.force_kill_comfyui()
```

### Advanced Usage

For direct texture generation from Python code:

```python
# Import the API
import dreamwave_texgen_api

# Create API instance
api = dreamwave_texgen_api.DreamwaveTexGenAPI()

# Generate a texture with a prompt and style
texture_path = api.generate_texture(
    prompt="colorful abstract pattern with swirls",
    style="Vaporwave",
    width=1024, 
    height=1024
)

# Import the generated texture into Unreal Engine (optional)
asset_path = api.import_texture(texture_path, "MyGeneratedTexture")
```

You can also use the FluxSchnell workflow directly for faster generation:

```python
# Access the bridge
bridge = api.bridge

# Generate using FluxSchnell
texture_path = bridge.generate_with_flux_workflow(
    prompt="vibrant abstract texture",
    negative_prompt="blurry, low quality",
    width=1024,
    height=1024
)
```

These commands provide programmatic control over the texture generation process and can be integrated into your own scripts and tools.

## License

Copyright © 2024 Dreamwave Synthesia. All rights reserved. 