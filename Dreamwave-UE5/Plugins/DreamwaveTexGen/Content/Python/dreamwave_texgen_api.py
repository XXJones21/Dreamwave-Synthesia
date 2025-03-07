"""
Dreamwave Texture Generator - Unreal Engine Python API

This module provides an interface between Unreal Engine and the ComfyUI server
for generating textures using AI models.
"""

import os
import sys
import json
import subprocess
import time
import tempfile
import unreal
import importlib
import uuid
from datetime import datetime
import random
import traceback
import webbrowser

# Try to import requests, install if missing
try:
    import requests
except ImportError:
    unreal.log_warning("Python module 'requests' not found. Attempting to install...")
    try:
        # Instead of using subprocess which might launch a new UE instance,
        # use Python's built-in pip functionality directly if available
        try:
            import pip
            pip.main(['install', 'requests'])
        except (ImportError, AttributeError):
            # Fallback to a more careful subprocess approach
            # Get the Python executable path used by Unreal
            python_exe = sys.executable
            
            # Create a detached process to run pip
            startupinfo = None
            if hasattr(subprocess, 'STARTUPINFO'):
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE
            
            # Run pip install with no window
            process = subprocess.Popen(
                [python_exe, "-m", "pip", "install", "requests"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                startupinfo=startupinfo,
                shell=False,  # Avoid using shell
                creationflags=0x08000000 if os.name == 'nt' else 0  # CREATE_NO_WINDOW on Windows
            )
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                unreal.log("Successfully installed 'requests' module")
            else:
                error_msg = stderr.decode('utf-8') if stderr else "Unknown error"
                unreal.log_error(f"Failed to install 'requests' module: {error_msg}")
                raise ImportError(error_msg)
                
        import requests
    except Exception as e:
        unreal.log_error(f"Failed to install 'requests' module: {str(e)}")
        unreal.log_warning("Falling back to built-in HTTP libraries")
        # Define a simple fallback using urllib
        import urllib.request
        import urllib.error
        import urllib.parse
        
        class RequestsFallback:
            @staticmethod
            def post(url, json=None, **kwargs):
                class Response:
                    def __init__(self, code, data):
                        self.status_code = code
                        self._data = data
                    
                    def json(self):
                        return json.loads(self._data.decode('utf-8'))
                    
                    def raise_for_status(self):
                        if self.status_code >= 400:
                            raise Exception(f"HTTP Error: {self.status_code}")
                
                data = json.dumps(json).encode('utf-8') if json else None
                headers = {'Content-Type': 'application/json'}
                req = urllib.request.Request(url, data=data, headers=headers)
                
                try:
                    with urllib.request.urlopen(req) as response:
                        return Response(response.code, response.read())
                except urllib.error.HTTPError as e:
                    return Response(e.code, e.read())
            
            @staticmethod
            def get(url, **kwargs):
                class Response:
                    def __init__(self, code, data):
                        self.status_code = code
                        self._data = data
                        self.content = data
                    
                    def json(self):
                        return json.loads(self._data.decode('utf-8'))
                    
                    def raise_for_status(self):
                        if self.status_code >= 400:
                            raise Exception(f"HTTP Error: {self.status_code}")
                
                req = urllib.request.Request(url)
                
                try:
                    with urllib.request.urlopen(req) as response:
                        return Response(response.code, response.read())
                except urllib.error.HTTPError as e:
                    return Response(e.code, e.read())
        
        # Replace requests with our fallback
        requests = RequestsFallback()

# Import settings
try:
    # Try to import from current directory first
    from dreamwave_texgen_settings import SETTINGS
    unreal.log("Successfully imported settings module")
except ImportError as e:
    unreal.log_warning(f"Failed to import settings module: {str(e)}")
    # Create a basic settings object as fallback
    class SettingsFallback:
        def __init__(self):
            self.ComfyUIServerURL = "http://127.0.0.1:8188"
            self.WorkflowFilePath = None
            self.OutputDirectory = None
            self.VaporwavePreset = "colorful, neon, retro, 80s, vaporwave, pastel colors, palm trees, grid"
            self.SynthwavePreset = "dark, neon, sci-fi, synthwave, purple, blue, cyber, retro futuristic"
            self.CyberpunkPreset = "cyberpunk, futuristic, high tech, neon lights, urban, dystopian, rainy"
            self.RetroPreset = "retro, vintage, old-school, pixelated, 8-bit, nostalgic"
    
    SETTINGS = SettingsFallback()

# Set up ComfyBridge import and initialization
BRIDGE_IMPORTED = False
try:
    # Add necessary paths to import our Python bridge
    script_dir = os.path.dirname(os.path.abspath(__file__))
    plugin_dir = os.path.dirname(os.path.dirname(script_dir))
    workspace_dir = os.path.dirname(os.path.dirname(plugin_dir))
    dreamwave_dir = os.path.join(workspace_dir, "dreamwave")
    
    if dreamwave_dir not in sys.path:
        sys.path.append(dreamwave_dir)
    
    # Try to import the ComfyBridge module
    try:
        from texture_gen.comfy_bridge import ComfyBridge
        BRIDGE_IMPORTED = True
        unreal.log(f"Successfully imported ComfyBridge from {dreamwave_dir}")
    except ImportError as e:
        unreal.log_warning(f"Failed to import ComfyBridge: {str(e)}")
except Exception as e:
    unreal.log_warning(f"Error setting up ComfyBridge path: {str(e)}")

class DreamwaveTexGenAPI:
    """API for generating textures from within Unreal Engine."""
    
    def __init__(self):
        """Initialize the API."""
        self.settings = SETTINGS
        self.bridge = None
        self.initialize_bridge()
    
    def initialize_bridge(self):
        """Initialize the ComfyUI bridge using plugin settings."""
        server_url = self.settings.ComfyUIServerURL
        if not server_url or server_url == "":
            server_url = "http://127.0.0.1:8188"
        
        unreal.log(f"Initializing ComfyUI bridge with server URL: {server_url}")
        
        if BRIDGE_IMPORTED:
            try:
                self.bridge = ComfyBridge(server_url=server_url)
                unreal.log("ComfyUI bridge initialized successfully")
            except Exception as e:
                unreal.log_error(f"Failed to initialize ComfyUI bridge: {str(e)}")
                self.bridge = None
        else:
            # Fallback to direct HTTP requests if bridge not available
            unreal.log("Using fallback HTTP implementation for ComfyUI")
            self.bridge = SimpleBridge(server_url)
    
    def get_workflow_path(self):
        """Get the path to the ComfyUI workflow file from settings."""
        workflow_path = self.settings.WorkflowFilePath if hasattr(self.settings, 'WorkflowFilePath') else None
        
        if not workflow_path or workflow_path == "":
            # Try to use the default workflow from the project
            script_dir = os.path.dirname(os.path.abspath(__file__))
            workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
            default_workflow = os.path.join(workspace_dir, "dreamwave", "workflows", "texture_gen_basic.json")
            
            if os.path.exists(default_workflow):
                unreal.log(f"Using default workflow: {default_workflow}")
                return default_workflow
            else:
                unreal.log_warning("No workflow file configured and default not found. Using built-in workflow.")
                return None
        else:
            unreal.log(f"Using configured workflow: {workflow_path}")
            return workflow_path
    
    def get_output_dir(self):
        """Get the output directory for saving textures."""
        output_dir = self.settings.OutputDirectory if hasattr(self.settings, 'OutputDirectory') else None
        
        if not output_dir or output_dir == "":
            # Use a default directory in the project's content folder
            project_dir = unreal.Paths.project_content_dir()
            output_dir = os.path.join(project_dir, "DreamwaveTextures")
            
            # Ensure the directory exists
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            unreal.log(f"Using default output directory: {output_dir}")
        else:
            unreal.log(f"Using configured output directory: {output_dir}")
        
        return output_dir
    
    def get_style_preset(self, style):
        """Get the style preset for a given style."""
        if style == "Vaporwave" and hasattr(self.settings, 'VaporwavePreset'):
            return self.settings.VaporwavePreset
        elif style == "Synthwave" and hasattr(self.settings, 'SynthwavePreset'):
            return self.settings.SynthwavePreset
        elif style == "Cyberpunk" and hasattr(self.settings, 'CyberpunkPreset'):
            return self.settings.CyberpunkPreset
        elif style == "Retro" and hasattr(self.settings, 'RetroPreset'):
            return self.settings.RetroPreset
        else:
            return None
    
    def generate_texture(self, prompt, style="Vaporwave", width=1024, height=1024):
        """Generate a texture using ComfyUI."""
        try:
            unreal.log(f"Generating texture with prompt: {prompt}, style: {style}, size: {width}x{height}")
            
            if not self.bridge:
                return "Error: ComfyUI bridge not initialized"
            
            # Create a unique texture ID
            texture_id = f"tex_{uuid.uuid4().hex[:8]}"
            
            # Prepare prompt with style
            style_prompt = self.get_style_preset(style)
            full_prompt = f"{prompt}, {style_prompt}" if style_prompt else prompt
            
            # Set negative prompt
            negative_prompt = "blurry, low quality, distorted, ugly"
            
            # Set the output path for the texture
            output_path = os.path.join(self.get_output_dir(), f"{texture_id}.png")
            
            unreal.log(f"Generating texture to: {output_path}")
            
            # Track if we encountered a connection error
            connection_error = None
            
            # Generate the texture using the appropriate method
            result_path = None
            
            try:
                # First try the consistent prompt_to_image interface which both bridge types should have
                if hasattr(self.bridge, 'prompt_to_image'):
                    result_path = self.bridge.prompt_to_image(
                        prompt=full_prompt,
                        negative_prompt=negative_prompt,
                        width=width,
                        height=height,
                        output_dir=self.get_output_dir()
                    )
                # Fallback to other methods
                elif hasattr(self.bridge, 'run_workflow_with_prompt'):
                    workflow_path = self.get_workflow_path()
                    if workflow_path:
                        result_path = self.bridge.run_workflow_with_prompt(
                            workflow_path=workflow_path,
                            prompt=full_prompt,
                            negative_prompt=negative_prompt,
                            width=width,
                            height=height,
                            output_path=output_path
                        )
                elif hasattr(self.bridge, 'generate_image'):
                    # Fallback to generate_image for SimpleBridge
                    success = self.bridge.generate_image(
                        prompt=full_prompt,
                        negative_prompt=negative_prompt,
                        width=width,
                        height=height,
                        output_path=output_path
                    )
                    if success:
                        result_path = output_path
                else:
                    return "Error: Bridge does not support texture generation"
            except Exception as conn_err:
                # Check if it's a connection error
                error_str = str(conn_err)
                if "connection" in error_str.lower() or "connect" in error_str.lower() or "refused" in error_str.lower():
                    connection_error = f"Error: Cannot connect to ComfyUI server at {self.bridge.server_url}. Please ensure ComfyUI is running."
                    unreal.log_error(f"ComfyUI Connection Error: {error_str}")
                    unreal.log_error(connection_error)
                    
                    # Show an error dialog with instructions
                    try:
                        unreal.EditorDialog.show_message(
                            title="ComfyUI Connection Error",
                            message=f"{connection_error}\n\nPlease start ComfyUI before generating textures.\n\nDetailed error: {error_str}",
                            message_type=unreal.AppMsgType.OK
                        )
                    except:
                        unreal.log_error("Please start ComfyUI before generating textures.")
                    
                    # Return the connection error directly - this is key to ensuring it propagates
                    return connection_error
                else:
                    # For other errors, re-raise to be caught by the outer handler
                    raise conn_err
            
            # Import the texture into Unreal Engine
            if result_path and os.path.exists(result_path):
                self.import_texture(result_path, texture_id)
                return f"Texture generated and imported: {texture_id}"
            else:
                # If we had a connection error, return that instead of generic error
                if connection_error:
                    return connection_error
                
                error_msg = "Error: Texture generation failed, file not found"
                unreal.log_error(error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            unreal.log_error(f"Exception in generate_texture: {str(e)}")
            return error_msg
    
    def import_texture(self, file_path, asset_name):
        """Import a texture from a file into Unreal Engine."""
        try:
            # Determine import location in content browser
            import_location = "/Game/DreamwaveTextures"
            
            # Ensure the destination directory exists in the content browser
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            asset_tools.make_directory(import_location)
            
            # Import the texture
            import_task = unreal.AssetImportTask()
            import_task.filename = file_path
            import_task.destination_path = import_location
            import_task.destination_name = asset_name
            import_task.replace_existing = True
            import_task.automated = True
            import_task.save = True
            
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([import_task])
            
            unreal.log(f"Texture imported to {import_location}/{asset_name}")
            
            # Open the imported texture in the content browser
            asset_path = f"{import_location}/{asset_name}.{asset_name}"
            unreal.EditorAssetLibrary.sync_browser_to_assets([asset_path])
            
            return asset_path
        except Exception as e:
            unreal.log_error(f"Error importing texture: {str(e)}")
            return None
        
    def launch_comfyui_server(self, show_dialog=True):
        """Launch the ComfyUI server if it's not already running."""
        try:
            # Try to connect to the existing server first
            server_url = self.settings.ComfyUIServerURL
            if not server_url or server_url == "":
                server_url = "http://127.0.0.1:8188"
                
            # Check if server is already running
            try:
                import requests
                response = requests.get(f"{server_url}/system_stats", timeout=2)
                if response.status_code == 200:
                    message = f"ComfyUI server is already running at {server_url}"
                    unreal.log(message)
                    
                    # Ask if user wants to open the UI
                    if show_dialog:
                        try:
                            dialog_result = unreal.EditorDialog.show_message(
                                title="ComfyUI Server",
                                message=f"{message}\n\nWould you like to open the ComfyUI web interface?",
                                message_type=unreal.AppMsgType.YES_NO
                            )
                            if dialog_result == unreal.AppReturnType.YES:
                                # Open ComfyUI in browser
                                webbrowser.open(server_url)
                        except:
                            unreal.log(message)
                            
                    return True
            except:
                # Server is not running, continue with launch
                pass
                
            # Look for ComfyUI installation
            # First check if there's a comfyui_path in settings
            comfyui_path = getattr(self.settings, 'ComfyUIPath', None)
            
            if not comfyui_path or not os.path.exists(comfyui_path):
                # Try to locate ComfyUI relative to our workspace
                script_dir = os.path.dirname(os.path.abspath(__file__))
                workspace_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir))))
                tools_dir = os.path.dirname(workspace_dir)  # Parent dir of workspace dir which might be "Tools"
                root_dir = os.path.dirname(tools_dir)  # Root drive or parent directory
                
                # Log directories for debugging
                unreal.log(f"Script directory: {script_dir}")
                unreal.log(f"Workspace directory: {workspace_dir}")
                unreal.log(f"Tools directory: {tools_dir}")
                
                # Common locations relative to workspace
                possible_locations = [
                    os.path.join(workspace_dir, "ComfyUI"),  
                    os.path.join(workspace_dir, "tools", "ComfyUI"),
                    os.path.join(workspace_dir, "Dreamwave-Synthesia", "ComfyUI"),
                    os.path.join(os.path.dirname(workspace_dir), "ComfyUI"),
                    # Add specific paths based on your file structure
                    os.path.join(tools_dir, "Dreamwave-Synthesia", "ComfyUI"),
                    os.path.join(workspace_dir, "ComfyUI", "ComfyUI_windows_portable", "ComfyUI"),
                    # Look for ComfyUI_windows_portable
                    os.path.join(workspace_dir, "ComfyUI_windows_portable", "ComfyUI"),
                    os.path.join(tools_dir, "Dreamwave-Synthesia", "ComfyUI", "ComfyUI_windows_portable", "ComfyUI"),
                    # Look for specific path seen in your structure
                    "D:\\Tools\\Dreamwave-Synthesia\\ComfyUI\\ComfyUI_windows_portable\\ComfyUI"
                ]
                
                # Check standard installation locations
                if os.name == 'nt':  # Windows
                    possible_locations.extend([
                        os.path.join(os.environ.get('APPDATA', ''), "ComfyUI"),
                        os.path.join(os.environ.get('LOCALAPPDATA', ''), "ComfyUI"),
                        "C:\\ComfyUI",
                        "D:\\ComfyUI",
                        # Additional typical Windows paths
                        "C:\\Program Files\\ComfyUI",
                        "C:\\Program Files (x86)\\ComfyUI",
                        "D:\\Program Files\\ComfyUI",
                        os.path.join(os.environ.get('USERPROFILE', ''), "Downloads", "ComfyUI")
                    ])
                else:  # macOS/Linux
                    home = os.environ.get('HOME', '')
                    possible_locations.extend([
                        os.path.join(home, "ComfyUI"),
                        os.path.join(home, "Applications", "ComfyUI"),
                        "/Applications/ComfyUI",
                        "/opt/ComfyUI"
                    ])
                
                # Find the first valid ComfyUI installation
                for location in possible_locations:
                    unreal.log(f"Checking for ComfyUI at: {location}")
                    main_py_path = os.path.join(location, "main.py")
                    if os.path.exists(main_py_path):
                        comfyui_path = location
                        unreal.log(f"Found ComfyUI main.py at: {main_py_path}")
                        break
            
            if not comfyui_path or not os.path.exists(comfyui_path):
                error_msg = "ComfyUI installation not found. Please install ComfyUI and set the path in settings."
                unreal.log_error(error_msg)
                
                # Create a settings file to directly set the path
                try:
                    settings_path = os.path.join(script_dir, "dreamwave_texgen_settings.py")
                    if not os.path.exists(settings_path):
                        unreal.log("Creating settings file to set ComfyUI path...")
                        # Prompt the user for the ComfyUI path
                        if show_dialog:
                            dialog_result = unreal.EditorDialog.show_message(
                                title="ComfyUI Not Found",
                                message=f"{error_msg}\n\nWould you like to specify the path to your ComfyUI installation?",
                                message_type=unreal.AppMsgType.YES_NO
                            )
                            
                            if dialog_result == unreal.AppReturnType.YES:
                                # Use dialog to get path
                                path_dialog = unreal.EditorDialog.open_directory(
                                    title="Select ComfyUI Installation Folder",
                                    default_path=workspace_dir
                                )
                                
                                if path_dialog and os.path.exists(path_dialog):
                                    # Check if the path contains main.py
                                    if os.path.exists(os.path.join(path_dialog, "main.py")):
                                        # Create settings file with the path
                                        with open(settings_path, "w") as f:
                                            f.write("class SETTINGS:\n")
                                            f.write(f"    ComfyUIServerURL = \"http://127.0.0.1:8188\"\n")
                                            f.write(f"    ComfyUIPath = r\"{path_dialog}\"\n")
                                            f.write(f"    OutputDirectory = None\n")
                                            f.write(f"    VaporwavePreset = \"colorful, neon, retro, 80s, vaporwave, pastel colors, palm trees, grid\"\n")
                                            f.write(f"    SynthwavePreset = \"dark, neon, sci-fi, synthwave, purple, blue, cyber, retro futuristic\"\n")
                                            f.write(f"    CyberpunkPreset = \"cyberpunk, futuristic, high tech, neon lights, urban, dystopian, rainy\"\n")
                                            f.write(f"    RetroPreset = \"retro, vintage, old-school, pixelated, 8-bit, nostalgic\"\n")
                                        
                                        unreal.log(f"Created settings file with ComfyUI path: {path_dialog}")
                                        
                                        # Reload settings
                                        try:
                                            importlib.reload(sys.modules['dreamwave_texgen_settings'])
                                            from dreamwave_texgen_settings import SETTINGS
                                            self.settings = SETTINGS
                                            comfyui_path = path_dialog
                                        except:
                                            unreal.log_warning("Failed to reload settings, please restart Unreal Editor")
                                    else:
                                        unreal.EditorDialog.show_message(
                                            title="Invalid ComfyUI Path",
                                            message=f"The selected folder does not contain 'main.py'. Please select the correct ComfyUI folder.",
                                            message_type=unreal.AppMsgType.OK
                                        )
                except Exception as settings_err:
                    unreal.log_error(f"Failed to create settings file: {str(settings_err)}")
                
                if not comfyui_path or not os.path.exists(comfyui_path):
                    if show_dialog:
                        try:
                            unreal.EditorDialog.show_message(
                                title="ComfyUI Not Found",
                                message=f"{error_msg}\n\nYou can download ComfyUI from: https://github.com/comfyanonymous/ComfyUI\n\nAfter installing, please place it in one of these locations:\n- {workspace_dir}\\ComfyUI\n- D:\\Tools\\Dreamwave-Synthesia\\ComfyUI",
                                message_type=unreal.AppMsgType.OK
                            )
                        except:
                            unreal.log_error(error_msg)
                            
                    return False
            
            # Check if ComfyUI is already running (one more time)
            try:
                import requests
                response = requests.get(f"{server_url}/system_stats", timeout=3)
                if response.status_code == 200:
                    message = f"ComfyUI server is already running at {server_url}"
                    unreal.log(message)
                    
                    # Ask if user wants to open the UI
                    if show_dialog:
                        try:
                            dialog_result = unreal.EditorDialog.show_message(
                                title="ComfyUI Server",
                                message=f"{message}\n\nWould you like to open the ComfyUI web interface?",
                                message_type=unreal.AppMsgType.YES_NO
                            )
                            if dialog_result == unreal.AppReturnType.YES:
                                # Open ComfyUI in browser
                                webbrowser.open(server_url)
                        except:
                            unreal.log(message)
                            
                    return True
            except:
                # Server is not running, continue with launch
                pass
                
            # Launch ComfyUI using subprocess
            unreal.log(f"Launching ComfyUI server from: {comfyui_path}")
            
            # Create a log file for the ComfyUI output
            log_dir = os.path.join(script_dir, "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"comfyui_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
            
            # Method 1: Use direct command-line start with output redirection (Windows-specific)
            if os.name == 'nt':  # Windows
                try:
                    import subprocess
                    import shlex
                    
                    # Get the actual Python executable from the ComfyUI folder if possible
                    python_exe = None
                    
                    # Try to find the Python executable inside the ComfyUI portable folder
                    # This helps avoid using the UE Python which can cause issues
                    possible_python_paths = [
                        os.path.join(os.path.dirname(comfyui_path), "python_embeded", "python.exe"),
                        os.path.join(os.path.dirname(comfyui_path), "python", "python.exe"),
                        os.path.join(os.path.dirname(os.path.dirname(comfyui_path)), "python_embeded", "python.exe"),
                        os.path.join(os.path.dirname(os.path.dirname(comfyui_path)), "python", "python.exe")
                    ]
                    
                    for py_path in possible_python_paths:
                        if os.path.exists(py_path):
                            python_exe = py_path
                            unreal.log(f"Using ComfyUI bundled Python: {python_exe}")
                            break
                    
                    # Fallback to system Python if needed
                    if not python_exe:
                        # Avoid using the UE Python interpreter
                        try:
                            # Try to find Python in the system PATH
                            find_python_process = subprocess.run(
                                ["where", "python"], 
                                capture_output=True, 
                                text=True,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            
                            if find_python_process.returncode == 0:
                                python_paths = find_python_process.stdout.strip().split('\n')
                                for path in python_paths:
                                    # Skip UE Python
                                    if "UE_" not in path and path.strip():
                                        python_exe = path.strip()
                                        unreal.log(f"Using system Python: {python_exe}")
                                        break
                        except Exception as path_err:
                            unreal.log_warning(f"Failed to find system Python: {str(path_err)}")
                    
                    # Last resort, use sys.executable but be cautious
                    if not python_exe:
                        python_exe = sys.executable
                        unreal.log_warning(f"Using UE Python as fallback (may cause issues): {python_exe}")
                    
                    # Check for required dependencies and install them if needed
                    if python_exe:
                        # Read requirements file to identify key dependencies
                        requirements_file = os.path.join(comfyui_path, "requirements.txt")
                        required_packages = []
                        
                        if os.path.exists(requirements_file):
                            with open(requirements_file, 'r') as f:
                                for line in f:
                                    line = line.strip()
                                    if line and not line.startswith('#'):
                                        required_packages.append(line.split('>=')[0].split('==')[0])
                        
                        # Always include these critical packages
                        critical_packages = ["torch", "torchvision", "pyyaml"]
                        for pkg in critical_packages:
                            if pkg not in required_packages:
                                required_packages.append(pkg)
                        
                        # Check if dependencies are installed
                        unreal.log(f"Checking for required dependencies...")
                        missing_packages = []
                        
                        for package in required_packages:
                            try:
                                # Run a python command to check if the package is importable
                                check_cmd = [
                                    python_exe, 
                                    "-c", 
                                    f"import {package}"
                                ]
                                result = subprocess.run(
                                    check_cmd,
                                    capture_output=True,
                                    text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                                
                                if result.returncode != 0:
                                    missing_packages.append(package)
                                    unreal.log(f"Missing package: {package}")
                            except Exception as e:
                                unreal.log(f"Error checking for {package}: {str(e)}")
                                missing_packages.append(package)
                        
                        # If using system Python, try to install missing dependencies
                        if missing_packages and "UE_" not in python_exe:
                            try:
                                # Show dialog asking permission to install packages
                                if show_dialog:
                                    install_msg = f"ComfyUI requires the following Python packages that are not installed:\n\n"
                                    install_msg += ", ".join(missing_packages)
                                    install_msg += "\n\nWould you like to install these packages now? This may take several minutes."
                                    
                                    dialog_result = unreal.EditorDialog.show_message(
                                        title="Missing Dependencies",
                                        message=install_msg,
                                        message_type=unreal.AppMsgType.YES_NO
                                    )
                                    
                                    if dialog_result == unreal.AppReturnType.YES:
                                        # Install missing packages
                                        for package in missing_packages:
                                            unreal.log(f"Installing {package}...")
                                            
                                            # Special case for PyTorch - use the official install command for Windows
                                            if package in ["torch", "torchvision", "torchaudio"]:
                                                install_cmd = [
                                                    python_exe,
                                                    "-m",
                                                    "pip",
                                                    "install",
                                                    "torch",
                                                    "torchvision",
                                                    "torchaudio",
                                                    "--index-url",
                                                    "https://download.pytorch.org/whl/cu118"
                                                ]
                                            else:
                                                install_cmd = [
                                                    python_exe,
                                                    "-m",
                                                    "pip",
                                                    "install",
                                                    package
                                                ]
                                            
                                            # Run installation
                                            result = subprocess.run(
                                                install_cmd,
                                                capture_output=True,
                                                text=True
                                            )
                                            
                                            if result.returncode == 0:
                                                unreal.log(f"Successfully installed {package}")
                                            else:
                                                unreal.log_error(f"Failed to install {package}: {result.stderr}")
                                    else:
                                        unreal.log("User chose not to install dependencies")
                                        
                                        # Show message about manual installation
                                        unreal.EditorDialog.show_message(
                                            title="Manual Installation Required",
                                            message=f"Please install the missing dependencies manually by running:\n\n{python_exe} -m pip install torch torchvision pyyaml\n\nThen try launching ComfyUI again.",
                                            message_type=unreal.AppMsgType.OK
                                        )
                                        return False
                            except Exception as install_err:
                                unreal.log_error(f"Error installing dependencies: {str(install_err)}")
                                unreal.log_error(traceback.format_exc())
                    
                    # Version 1: Use a batch file that redirects output to a log file
                    batch_file = os.path.join(script_dir, "launch_comfyui.bat")
                    with open(batch_file, "w") as f:
                        # Use proper quoting for paths with spaces
                        f.write(f'@echo off\n')
                        f.write(f'echo Starting ComfyUI server...\n')
                        f.write(f'cd /d "{comfyui_path}"\n')
                        # Redirect output to log file
                        f.write(f'"{python_exe}" "{os.path.join(comfyui_path, "main.py")}" --listen 127.0.0.1 --port 8188 > "{log_file}" 2>&1\n')
                        f.write(f'echo Server started. Log file: {log_file}\n')
                        f.write(f'exit\n')
                    
                    # Make the batch file executable
                    os.chmod(batch_file, 0o755)
                    
                    # Start the batch file with no window
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                    
                    # Run the batch file directly
                    subprocess.Popen(
                        [batch_file],
                        cwd=os.path.dirname(batch_file),
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    unreal.log(f"Started ComfyUI server using batch file. Log: {log_file}")
                    
                except Exception as e:
                    unreal.log_error(f"Error launching ComfyUI with batch file: {str(e)}")
                    unreal.log_error(traceback.format_exc())
                    
                    # Fallback to powershell if batch method fails
                    try:
                        unreal.log("Attempting to launch with PowerShell...")
                        
                        # This uses PowerShell which is more reliable for some setups
                        powershell_cmd = f'powershell.exe -Command "Start-Process -FilePath \'{python_exe}\' -ArgumentList \'{os.path.join(comfyui_path, "main.py")}\', \'--listen\', \'127.0.0.1\', \'--port\', \'8188\' -WorkingDirectory \'{comfyui_path}\' -WindowStyle Hidden"'
                        
                        subprocess.Popen(
                            powershell_cmd,
                            shell=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        
                        unreal.log("Started ComfyUI server using PowerShell")
                    except Exception as ps_err:
                        unreal.log_error(f"Error launching with PowerShell: {str(ps_err)}")
                        unreal.log_error(traceback.format_exc())
                        
                        # Absolute last resort - direct subprocess call
                        try:
                            startupinfo = subprocess.STARTUPINFO()
                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                            startupinfo.wShowWindow = 0  # SW_HIDE
                            
                            subprocess.Popen(
                                [python_exe, os.path.join(comfyui_path, "main.py"), "--listen", "127.0.0.1", "--port", "8188"],
                                cwd=comfyui_path,
                                startupinfo=startupinfo,
                                creationflags=subprocess.CREATE_NO_WINDOW,
                                shell=False
                            )
                            
                            unreal.log("Started ComfyUI server using direct subprocess call")
                        except Exception as last_err:
                            unreal.log_error(f"All launch methods failed: {str(last_err)}")
                            unreal.log_error(traceback.format_exc())
                            
                            if show_dialog:
                                unreal.EditorDialog.show_message(
                                    title="ComfyUI Launch Failed",
                                    message="All automated launch methods failed. Please try launching ComfyUI manually.",
                                    message_type=unreal.AppMsgType.OK
                                )
                            return False
            else:  # macOS/Linux
                # Use subprocess.Popen to start in background
                import subprocess
                process = subprocess.Popen(
                    [sys.executable, os.path.join(comfyui_path, "main.py"), "--listen", "127.0.0.1", "--port", "8188"],
                    cwd=comfyui_path,
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
            
            # Wait for the server to start up (with a longer timeout)
            server_started = False
            max_retries = 20  # Try for 60 seconds total (increased from 10)
            retry_delay = 3   # 3 seconds between retries
            
            # Show a waiting message immediately
            if show_dialog:
                message = "Starting ComfyUI server. This may take a minute...\n\nPlease wait while the server initializes."
                try:
                    unreal.EditorDialog.show_message(
                        title="Starting ComfyUI",
                        message=message,
                        message_type=unreal.AppMsgType.OK
                    )
                except:
                    unreal.log(message)
            
            # Now wait for the server to respond
            for retry in range(max_retries):
                try:
                    unreal.log(f"Checking if ComfyUI server is up (attempt {retry+1}/{max_retries})...")
                    
                    # Read log file if available to diagnose issues
                    if os.path.exists(log_file) and os.path.getsize(log_file) > 0:
                        try:
                            with open(log_file, 'r') as f:
                                recent_logs = f.readlines()[-10:]  # Get last 10 lines
                                unreal.log(f"Recent ComfyUI logs: {' '.join(recent_logs).strip()}")
                        except Exception as log_err:
                            unreal.log_warning(f"Could not read log file: {str(log_err)}")
                    
                    import requests
                    response = requests.get(f"{server_url}/system_stats", timeout=5)
                    if response.status_code == 200:
                        server_started = True
                        break
                except Exception as e:
                    unreal.log(f"Server not yet running, waiting... ({retry+1}/{max_retries})")
                
                # Wait before retrying
                time.sleep(retry_delay)
            
            # Final status report
            if server_started:
                message = f"ComfyUI server has been launched at {server_url}"
                unreal.log(message)
                
                # Ask if user wants to open the UI in browser
                if show_dialog:
                    try:
                        dialog_result = unreal.EditorDialog.show_message(
                            title="ComfyUI Server Launched",
                            message=f"{message}\n\nWould you like to open the ComfyUI web interface?",
                            message_type=unreal.AppMsgType.YES_NO
                        )
                        
                        if dialog_result == unreal.AppReturnType.YES:
                            # Open ComfyUI in browser
                            webbrowser.open(server_url)
                    except:
                        unreal.log(message)
                        
                return True
            else:
                error_msg = f"ComfyUI server was started but is not responding at {server_url}"
                unreal.log_error(error_msg)
                
                # Check if we should try to open the browser anyway
                if show_dialog:
                    try:
                        dialog_result = unreal.EditorDialog.show_message(
                            title="ComfyUI Server Timeout",
                            message=f"{error_msg}\n\nSometimes ComfyUI takes longer to start than expected. Would you like to try opening the web interface anyway?",
                            message_type=unreal.AppMsgType.YES_NO
                        )
                        
                        if dialog_result == unreal.AppReturnType.YES:
                            # Open ComfyUI in browser
                            webbrowser.open(server_url)
                            return True
                    except:
                        unreal.log_error(error_msg)
                
                # If all else fails, provide manual instructions
                try:
                    unreal.EditorDialog.show_message(
                        title="Manual ComfyUI Launch",
                        message=f"Automatic launch of ComfyUI failed, but you can try to start it manually:\n\n1. Open a command prompt\n2. Navigate to: {comfyui_path}\n3. Run: {python_exe} main.py\n\nAfter starting it manually, try using the plugin again.",
                        message_type=unreal.AppMsgType.OK
                    )
                except:
                    pass
                    
                return False
                
        except Exception as e:
            unreal.log_error(f"Error launching ComfyUI server: {str(e)}")
            unreal.log_error(traceback.format_exc())
            return False

class SimpleBridge:
    """A simplified version of the ComfyUI bridge using direct HTTP requests."""
    
    def __init__(self, server_url):
        """Initialize the simple bridge."""
        self.server_url = server_url
        self.api_url = f"{server_url}/api"
        self.client_id = str(uuid.uuid4())
        unreal.log(f"SimpleBridge initialized with server URL: {server_url}")
    
    def prompt_to_image(self, prompt, negative_prompt="", width=1024, height=1024, output_dir=None):
        """
        Generate an image from a prompt - compatible with ComfyBridge interface.
        """
        try:
            # Set default output path if not provided
            if not output_dir:
                output_dir = tempfile.gettempdir()
            
            # Create a unique output filename
            filename = f"dreamwave_{uuid.uuid4().hex[:8]}.png"
            output_path = os.path.join(output_dir, filename)
            
            # Call the internal generate_image method
            try:
                success = self.generate_image(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=width,
                    height=height,
                    output_path=output_path
                )
            except Exception as e:
                # Check for connection issues
                error_str = str(e)
                if "connection" in error_str.lower() or "connect" in error_str.lower():
                    # Add more descriptive message about ComfyUI connection
                    unreal.log_error(f"ComfyUI Connection Error: {error_str}")
                    unreal.log_error("Please ensure ComfyUI is running at http://127.0.0.1:8188")
                # Re-raise for consistent error handling
                raise
            
            # Return the output path if successful
            if success and os.path.exists(output_path):
                return output_path
            return None
        except Exception as e:
            unreal.log_error(f"Error in prompt_to_image: {str(e)}")
            # Re-raise to allow outer handlers to handle it
            raise
    
    def generate_image(self, prompt, negative_prompt="", width=1024, height=1024, output_path=None):
        """Generate an image using a simple predefined workflow."""
        try:
            # Create a simple workflow
            workflow = {
                "3": {
                    "inputs": {
                        "seed": random.randint(1, 999999999),
                        "steps": 20,
                        "cfg": 7.0,
                        "sampler_name": "euler_a",
                        "scheduler": "normal",
                        "denoise": 1.0,
                        "model": ["4", 0],
                        "positive": ["6", 0],
                        "negative": ["7", 0],
                        "latent_image": ["5", 0]
                    },
                    "class_type": "KSampler"
                },
                "4": {
                    "inputs": {
                        "ckpt_name": "dreamshaper_8.safetensors" 
                    },
                    "class_type": "CheckpointLoaderSimple"
                },
                "5": {
                    "inputs": {
                        "width": width,
                        "height": height,
                        "batch_size": 1
                    },
                    "class_type": "EmptyLatentImage"
                },
                "6": {
                    "inputs": {
                        "text": prompt,
                        "clip": ["4", 1]
                    },
                    "class_type": "CLIPTextEncode"
                },
                "7": {
                    "inputs": {
                        "text": negative_prompt,
                        "clip": ["4", 1]
                    },
                    "class_type": "CLIPTextEncode"
                },
                "8": {
                    "inputs": {
                        "samples": ["3", 0],
                        "vae": ["4", 2]
                    },
                    "class_type": "VAEDecode"
                },
                "9": {
                    "inputs": {
                        "filename_prefix": "dreamwave",
                        "images": ["8", 0]
                    },
                    "class_type": "SaveImage"
                }
            }
            
            # Set up the request
            prompt_api = f"{self.server_url}/prompt"
            unreal.log(f"Sending generation request to ComfyUI...")
            
            try:
                # Post the workflow
                prompt_response = self.requests.post(prompt_api, json={"prompt": workflow})
                prompt_response.raise_for_status()
                
                # Get the prompt ID
                prompt_id = prompt_response.json().get("prompt_id")
                if not prompt_id:
                    unreal.log_error("No prompt ID returned from ComfyUI")
                    return False
                
                # Poll for completion
                history_api = f"{self.server_url}/history/{prompt_id}"
                max_wait = 120  # Maximum wait time in seconds
                start_time = time.time()
                
                while (time.time() - start_time) < max_wait:
                    # Check status
                    history_response = self.requests.get(history_api)
                    if history_response.status_code == 200:
                        history = history_response.json()
                        
                        # Check if completed
                        if prompt_id in history and "outputs" in history[prompt_id]:
                            # Find the output image
                            for node_id, node_output in history[prompt_id]["outputs"].items():
                                if node_id == "9" and "images" in node_output:
                                    # Get the first image
                                    image_data = node_output["images"][0]
                                    image_filename = image_data["filename"]
                                    image_url = f"{self.server_url}/view?filename={image_filename}"
                                    
                                    # Download the image
                                    image_response = self.requests.get(image_url)
                                    image_response.raise_for_status()
                                    
                                    # Save to output path
                                    if output_path:
                                        with open(output_path, "wb") as f:
                                            f.write(image_response.content)
                                        unreal.log(f"Image saved to {output_path}")
                                        return True
                                    else:
                                        unreal.log_error("No output path specified")
                                        return False
                    
                    # Sleep before checking again
                    time.sleep(1)
                
                unreal.log_error(f"Timed out waiting for ComfyUI to process prompt")
                return False
                
            except Exception as e:
                error_str = str(e)
                if "connection" in error_str.lower() or "connect" in error_str.lower() or "refused" in error_str.lower():
                    unreal.log_error(f"ComfyUI connection error: {error_str}")
                    unreal.log_error(f"Please make sure ComfyUI is running at {self.server_url}")
                else:
                    unreal.log_error(f"Error communicating with ComfyUI: {error_str}")
                # Re-raise to allow consistent error handling
                raise
        except Exception as e:
            unreal.log_error(f"Error in generate_image: {str(e)}")
            # Re-raise to allow consistent error handling
            raise

# Create a global instance for easy access from Unreal
api = DreamwaveTexGenAPI()

# Export functions for use in Unreal
def generate_texture(prompt, style_presets=None):
    """Generate a texture from a text prompt."""
    return api.generate_texture(prompt, style_presets)

def import_texture_to_unreal(texture_path, asset_name=None, asset_path=None):
    """Import a generated texture into Unreal Engine."""
    return api.import_texture_to_unreal(texture_path, asset_name, asset_path)

def generate_and_import(prompt, style_presets=None, asset_name=None, asset_path=None):
    """Generate a texture and import it into Unreal Engine."""
    return api.generate_and_import(prompt, style_presets, asset_name, asset_path) 