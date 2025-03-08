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
import threading
import queue

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

# Try to import the websocket module for real-time updates
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    unreal.log_warning("websocket-client module not found. Install it for real-time progress updates.")
    WEBSOCKET_AVAILABLE = False

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
        self.bridge = None
except Exception as e:
    unreal.log_warning(f"Error setting up ComfyBridge path: {str(e)}")

class DreamwaveTexGenAPI:
    """API for generating textures from within Unreal Engine."""
    
    # Class variable to track the ComfyUI server process across instances
    _comfyui_process = None
    _comfyui_batch_file = None
    _is_shutting_down_registered = False
    _pid_file = None  # Path to PID file for tracking server process
    _kill_script_file = None  # Path to the kill script
    
    def __init__(self):
        """Initialize the API."""
        # Register shutdown handler if not already registered
        if not DreamwaveTexGenAPI._is_shutting_down_registered:
            self._register_shutdown_handler()
            DreamwaveTexGenAPI._is_shutting_down_registered = True
            
        # If there's no stored PID file path, create one
        if not DreamwaveTexGenAPI._pid_file:
            # Store it in a predictable location
            script_dir = os.path.dirname(os.path.abspath(__file__))
            DreamwaveTexGenAPI._pid_file = os.path.join(script_dir, "comfyui_server.pid")
            DreamwaveTexGenAPI._kill_script_file = os.path.join(script_dir, "kill_comfyui_server.bat")
            
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
                # First check if we should use FluxSchnell workflow
                use_flux = hasattr(self.settings, 'UseFluxWorkflow') and self.settings.UseFluxWorkflow
                
                if use_flux and hasattr(self.bridge, 'generate_with_flux_workflow'):
                    unreal.log("Attempting to use FluxSchnell workflow for high-quality generation")
                    result_path = self.bridge.generate_with_flux_workflow(
                        prompt=full_prompt,
                        negative_prompt=negative_prompt,
                        width=width, 
                        height=height,
                        output_dir=self.get_output_dir()
                    )
                    
                    if result_path:
                        unreal.log("Successfully generated texture with FluxSchnell workflow")
                    else:
                        unreal.log_warning("FluxSchnell workflow failed, falling back to standard methods")
                
                # If FluxSchnell failed or wasn't used, try other methods
                if not result_path:
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
        """Launch the ComfyUI server."""
        # First check if the server is already running
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
                    
                    # Start the batch file directly
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                    
                    # Run the batch file directly
                    process = subprocess.Popen(
                        [batch_file],
                        cwd=os.path.dirname(batch_file),
                        startupinfo=startupinfo,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    
                    # Store the process and batch file for later cleanup
                    DreamwaveTexGenAPI._comfyui_process = process
                    DreamwaveTexGenAPI._comfyui_batch_file = batch_file
                    
                    # We don't have the actual Python process PID here yet
                    # We'll capture it after verifying the server is running
                    
                    unreal.log(f"Started ComfyUI server using batch file. Log: {log_file}")
                    
                except Exception as e:
                    unreal.log_error(f"Error launching ComfyUI with batch file: {str(e)}")
                    unreal.log_error(traceback.format_exc())
                    
                    # Fallback to powershell if batch method fails
                    try:
                        unreal.log("Attempting to launch with PowerShell...")
                        
                        # This uses PowerShell which is more reliable for some setups
                        powershell_cmd = f'powershell.exe -Command "Start-Process -FilePath \'{python_exe}\' -ArgumentList \'{os.path.join(comfyui_path, "main.py")}\', \'--listen\', \'127.0.0.1\', \'--port\', \'8188\' -WorkingDirectory \'{comfyui_path}\' -WindowStyle Hidden"'
                        
                        process = subprocess.Popen(
                            powershell_cmd,
                            shell=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        
                        # Store the process for later cleanup
                        DreamwaveTexGenAPI._comfyui_process = process
                        
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
                
                # Store the process for later cleanup
                DreamwaveTexGenAPI._comfyui_process = process
            
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
            
            # Try to connect to the server to verify it's running
            for i in range(max_retries):
                unreal.log(f"Waiting for ComfyUI server to start (attempt {i+1}/{max_retries})...")
                
                try:
                    import requests
                    response = requests.get(f"{server_url}/system_stats", timeout=5)
                    
                    if response.status_code == 200:
                        server_started = True
                        unreal.log("ComfyUI server is now running!")
                        
                        # Now that the server is running, find its PID and save to file
                        try:
                            import psutil
                            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                                try:
                                    cmdline = proc.info.get('cmdline', [])
                                    if cmdline and any('python' in cmd.lower() for cmd in cmdline) and any('main.py' in cmd for cmd in cmdline):
                                        server_pid = proc.info['pid']
                                        unreal.log(f"Found ComfyUI server process with PID: {server_pid}")
                                        # Save to PID file
                                        self._write_pid_file(server_pid)
                                        break
                                except:
                                    continue
                        except ImportError:
                            unreal.log_warning("psutil module not available - cannot save server PID")
                        except Exception as e:
                            unreal.log_warning(f"Could not find or save ComfyUI server PID: {e}")
                        
                        break
                        
                except Exception as e:
                    # Wait before trying again
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

    def _install_websocket_client(self):
        """Install the websocket-client module for the current Python environment."""
        try:
            import sys
            import subprocess
            
            # Get the path to the Python executable used by Unreal
            python_exe = sys.executable
            
            # Use subprocess to run pip
            unreal.log(f"Installing websocket-client using Python at: {python_exe}")
            subprocess.check_call([python_exe, "-m", "pip", "install", "websocket-client"])
            unreal.log("Successfully installed websocket-client module")
            
            # Try importing to verify
            import websocket
            return True
        except Exception as e:
            unreal.log_error(f"Failed to install websocket-client: {str(e)}")
            unreal.log_warning("Real-time progress updates will not be available")
            return False

    def _install_psutil(self):
        """Install the psutil module for process management."""
        try:
            import sys
            import subprocess
            
            # Get the path to the Python executable used by Unreal
            python_exe = sys.executable
            
            # Use subprocess to run pip
            unreal.log(f"Installing psutil using Python at: {python_exe}")
            subprocess.check_call([python_exe, "-m", "pip", "install", "psutil"])
            unreal.log("Successfully installed psutil module")
            
            # Try importing to verify
            import psutil
            return True
        except Exception as e:
            unreal.log_error(f"Failed to install psutil: {str(e)}")
            unreal.log_warning("Process management for ComfyUI may be limited")
            return False

    def _register_shutdown_handler(self):
        """Register a handler to shut down ComfyUI when Unreal Engine closes."""
        try:
            # Create Windows-specific cleanup script for maximum reliability
            if os.name == 'nt':
                self._create_kill_script()
            
            # Try to register with all available methods for maximum reliability
            
            # Method 1: Register with Unreal's tick callback if available
            if hasattr(unreal, 'register_slate_post_tick_callback'):
                unreal.log("Registering ComfyUI shutdown handler with Unreal tick callback")
                
                def check_unreal_shutdown(delta_time):
                    # Check if Unreal is in the process of shutting down
                    if hasattr(unreal, 'is_editor_shutting_down') and unreal.is_editor_shutting_down():
                        unreal.log("Unreal Editor is shutting down (detected by tick), closing ComfyUI server...")
                        DreamwaveTexGenAPI.shutdown_comfyui_server()
                        return False  # Stop the callback
                    return True  # Continue checking
                
                unreal.register_slate_post_tick_callback(check_unreal_shutdown)
            
            # Method 2: Always use atexit as well for redundancy
            unreal.log("Registering ComfyUI shutdown handler with atexit")
            import atexit
            atexit.register(DreamwaveTexGenAPI.shutdown_comfyui_server)
            
            # Method 3: Try to use Python's signal handlers for additional safety
            try:
                import signal
                # Register SIGTERM handler (normal termination)
                def handle_signal(sig, frame):
                    unreal.log(f"Received signal {sig}, shutting down ComfyUI server...")
                    DreamwaveTexGenAPI.shutdown_comfyui_server()
                
                signal.signal(signal.SIGTERM, handle_signal)
                # Register SIGINT handler (interrupt from keyboard)
                signal.signal(signal.SIGINT, handle_signal)
                unreal.log("Registered signal handlers for ComfyUI shutdown")
            except Exception as e:
                unreal.log_warning(f"Could not register signal handlers: {e}")
            
        except Exception as e:
            unreal.log_warning(f"Failed to register shutdown handlers: {e}")
            
    @classmethod
    def _write_pid_file(cls, pid):
        """Write the ComfyUI server process ID to the PID file."""
        try:
            with open(cls._pid_file, 'w') as f:
                f.write(str(pid))
            unreal.log(f"Wrote ComfyUI server PID {pid} to {cls._pid_file}")
        except Exception as e:
            unreal.log_warning(f"Failed to write PID file: {e}")
    
    @classmethod
    def _read_pid_file(cls):
        """Read the ComfyUI server process ID from the PID file."""
        try:
            if os.path.exists(cls._pid_file):
                with open(cls._pid_file, 'r') as f:
                    pid = int(f.read().strip())
                unreal.log(f"Read ComfyUI server PID {pid} from {cls._pid_file}")
                return pid
            else:
                unreal.log_warning(f"PID file {cls._pid_file} not found")
                return None
        except Exception as e:
            unreal.log_warning(f"Failed to read PID file: {e}")
            return None
    
    @classmethod
    def _remove_pid_file(cls):
        """Remove the ComfyUI server PID file."""
        try:
            if os.path.exists(cls._pid_file):
                os.remove(cls._pid_file)
                unreal.log(f"Removed PID file {cls._pid_file}")
        except Exception as e:
            unreal.log_warning(f"Failed to remove PID file: {e}")

    @classmethod
    def shutdown_comfyui_server(cls):
        """Shut down the ComfyUI server if it's running."""
        import os
        import subprocess
        import time
        
        unreal.log("Attempting to shut down ComfyUI server...")
        killed = False
        
        # Method 1: Try to terminate our tracked process
        if cls._comfyui_process is not None:
            unreal.log(f"Shutting down tracked ComfyUI process...")
            if hasattr(cls._comfyui_process, 'terminate'):
                try:
                    cls._comfyui_process.terminate()
                    # Wait a moment to let it terminate gracefully
                    time.sleep(1)
                    
                    # Check if it's still running
                    if hasattr(cls._comfyui_process, 'poll') and cls._comfyui_process.poll() is None:
                        # Force kill if still running
                        unreal.log("Process didn't terminate gracefully, forcing kill...")
                        if hasattr(cls._comfyui_process, 'kill'):
                            cls._comfyui_process.kill()
                    
                    cls._comfyui_process = None
                    killed = True
                except Exception as e:
                    unreal.log_warning(f"Error terminating tracked process: {e}")
        
        # Method 2: Check PID file (only if psutil is available)
        try:
            import psutil
            has_psutil = True
        except ImportError:
            has_psutil = False
            unreal.log_warning("psutil module not available, some termination methods will be skipped")
            
        if has_psutil:
            pid = cls._read_pid_file()
            if pid is not None:
                try:
                    unreal.log(f"Attempting to terminate process with PID {pid}...")
                    # Check if process exists
                    if psutil.pid_exists(pid):
                        process = psutil.Process(pid)
                        process.terminate()
                        # Wait for graceful termination
                        try:
                            process.wait(timeout=3)
                            killed = True
                        except psutil.TimeoutExpired:
                            # Force kill if it didn't terminate
                            unreal.log(f"Process {pid} didn't terminate gracefully, killing...")
                            process.kill()
                            killed = True
                except psutil.NoSuchProcess:
                    unreal.log(f"Process with PID {pid} not found")
                except Exception as e:
                    unreal.log_warning(f"Error terminating process {pid}: {e}")
            
            # Method 3: Find and kill Python processes running main.py
            try:
                unreal.log("Searching for ComfyUI processes...")
                for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                    try:
                        # Check if this is a Python process running ComfyUI
                        cmdline = proc.info.get('cmdline', [])
                        if cmdline and (any('python' in cmd.lower() for cmd in cmdline) or proc.info['name'].lower() == 'python.exe'):
                            if any('main.py' in cmd for cmd in cmdline) and any(arg in ["--port", "8188"] for arg in cmdline):
                                proc_pid = proc.info['pid']
                                unreal.log(f"Found ComfyUI process (PID: {proc_pid}), terminating...")
                                proc_obj = psutil.Process(proc_pid)
                                proc_obj.terminate()
                                
                                # Wait for graceful termination
                                try:
                                    proc_obj.wait(timeout=3)
                                except psutil.TimeoutExpired:
                                    # Force kill if it didn't terminate
                                    unreal.log(f"Process {proc_pid} didn't terminate gracefully, killing...")
                                    proc_obj.kill()
                                
                                killed = True
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
                        unreal.log_warning(f"Process error: {e}")
                    except Exception as e:
                        unreal.log_warning(f"Error processing {proc.info['pid'] if 'pid' in proc.info else 'unknown'}: {e}")
            except Exception as e:
                unreal.log_warning(f"Error searching for ComfyUI processes: {e}")
            
            # Method 4: Kill by TCP port (last resort if psutil available)
            try:
                unreal.log("Looking for processes using port 8188...")
                for conn in psutil.net_connections(kind='inet'):
                    if conn.laddr.port == 8188:
                        try:
                            unreal.log(f"Found process using port 8188 (PID: {conn.pid}), terminating...")
                            proc = psutil.Process(conn.pid)
                            proc.terminate()
                            try:
                                proc.wait(timeout=3)
                            except psutil.TimeoutExpired:
                                proc.kill()
                            killed = True
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
            except Exception as e:
                unreal.log_warning(f"Error checking network connections: {e}")
        
        # Method 5: Use direct Windows commands (available without psutil)
        if os.name == 'nt':  # Windows
            try:
                unreal.log("Attempting Windows-specific termination methods...")
                
                # Use the kill script directly if it exists
                if cls._kill_script_file and os.path.exists(cls._kill_script_file):
                    try:
                        unreal.log(f"Executing kill script: {cls._kill_script_file}")
                        subprocess.call(
                            [cls._kill_script_file],
                            shell=True,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        killed = True
                    except Exception as e:
                        unreal.log_warning(f"Error executing kill script: {e}")
                
                # Use netstat to find processes on port 8188
                try:
                    unreal.log("Using netstat to find processes on port 8188...")
                    netstat_output = subprocess.check_output(
                        "netstat -ano | findstr :8188", 
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    ).decode('utf-8')
                    
                    lines = netstat_output.strip().split('\n')
                    for line in lines:
                        if '8188' in line:
                            try:
                                pid = line.strip().split()[-1]
                                unreal.log(f"Found process on port 8188 with PID {pid}, terminating...")
                                subprocess.call(
                                    f"taskkill /F /PID {pid}", 
                                    shell=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW
                                )
                                killed = True
                            except Exception as e:
                                unreal.log_warning(f"Error terminating process from netstat: {e}")
                except Exception as e:
                    unreal.log_warning(f"Error using netstat: {e}")
                
                # Use wmic to find Python processes running main.py
                try:
                    unreal.log("Using wmic to find Python processes running main.py...")
                    subprocess.call(
                        'wmic process where "commandline like \'%main.py%\'" call terminate',
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    killed = True
                except Exception as e:
                    unreal.log_warning(f"Error using wmic: {e}")
                    
            except Exception as e:
                unreal.log_warning(f"Error in Windows-specific termination: {e}")
        
        # Method 6: Clean up batch file if we have it
        if cls._comfyui_batch_file and os.path.exists(cls._comfyui_batch_file):
            try:
                os.remove(cls._comfyui_batch_file)
                unreal.log(f"Removed ComfyUI batch file: {cls._comfyui_batch_file}")
            except Exception as e:
                unreal.log_warning(f"Failed to remove batch file: {e}")
            cls._comfyui_batch_file = None
        
        # Remove PID file
        cls._remove_pid_file()
        
        if killed:
            unreal.log("Successfully shut down ComfyUI server")
        else:
            unreal.log("No running ComfyUI server found to shut down")
            
        return killed

    @classmethod
    def _create_kill_script(cls):
        """Create a Windows batch file that will kill the ComfyUI server process even if Unreal crashes."""
        if os.name != 'nt':  # Windows only
            return
            
        try:
            # Create a batch file that kills any ComfyUI processes
            with open(cls._kill_script_file, 'w') as f:
                f.write('@echo off\n')
                f.write('echo Terminating ComfyUI server processes...\n')
                
                # Kill processes using port 8188
                f.write('for /f "tokens=5" %%a in (\'netstat -ano ^| findstr :8188\') do (\n')
                f.write('    taskkill /F /PID %%a\n')
                f.write('    echo Terminated process: %%a\n')
                f.write(')\n\n')
                
                # Kill Python processes running main.py
                f.write('for /f "tokens=2" %%p in (\'wmic process where "commandline like \'%%main.py%%\'" get processid /value ^| findstr "="\') do (\n')
                f.write('    set pid=%%p\n')
                f.write('    taskkill /F /PID %%p\n')
                f.write('    echo Terminated Python process: %%p\n')
                f.write(')\n\n')
                
                # Remove PID file if it exists
                f.write(f'if exist "{cls._pid_file}" del "{cls._pid_file}"\n')
                
                # Self-delete this script after execution
                f.write('(goto) 2>nul & del "%~f0"\n')
                
            unreal.log(f"Created ComfyUI kill script at {cls._kill_script_file}")
            
            # Make it executable
            os.chmod(cls._kill_script_file, 0o755)
            
            # We'll no longer start a watcher process automatically since it's causing Unreal Engine to relaunch
            unreal.log("Kill script created but not automatically started to avoid Unreal relaunch issues")
            unreal.log("The shutdown_comfyui command can be used to manually terminate the server")
                
        except Exception as e:
            unreal.log_warning(f"Failed to create kill script: {e}")

class SimpleBridge:
    """A simplified version of the ComfyUI bridge using direct HTTP requests."""
    
    def __init__(self, server_url):
        """Initialize the simple bridge."""
        self.server_url = server_url
        self.api_url = f"{server_url}/api"
        self.client_id = str(uuid.uuid4())
        
        # WebSocket and status tracking
        self.ws = None
        self.ws_thread = None
        self.message_queue = queue.Queue()
        self.execution_status = {}
        self.generation_id = None  # For tracking current generation
        
        unreal.log(f"SimpleBridge initialized with server URL: {server_url}")
        
    def connect_websocket(self):
        """Connect to the ComfyUI server websocket for real-time updates.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if not WEBSOCKET_AVAILABLE:
            unreal.log_warning("WebSocket not available - install websocket-client module for progress updates")
            return False
            
        if self.ws:
            unreal.log("WebSocket connection already exists")
            return True
            
        try:
            # Convert HTTP URL to WebSocket URL
            if self.server_url.startswith('https'):
                ws_url = f"wss://{self.server_url[8:]}/ws?clientId={self.client_id}"
            else:
                ws_url = f"ws://{self.server_url[7:]}/ws?clientId={self.client_id}"
                
            unreal.log(f"Connecting to WebSocket at {ws_url}")
            self.ws = websocket.create_connection(ws_url, timeout=10)
            unreal.log(f"Connected to ComfyUI websocket with client ID: {self.client_id}")
            
            # Start listener thread for websocket messages
            self._start_ws_listener()
            return True
            
        except Exception as e:
            unreal.log_error(f"Failed to connect to websocket: {e}")
            self.ws = None
            return False
            
    def disconnect_websocket(self):
        """Disconnect from the ComfyUI websocket."""
        if self.ws:
            try:
                self.ws.close()
                unreal.log("Disconnected from ComfyUI websocket")
            except Exception as e:
                unreal.log_error(f"Error disconnecting from websocket: {e}")
            finally:
                self.ws = None
                
    def _start_ws_listener(self):
        """Start a background thread to listen for websocket messages."""
        if not self.ws:
            return
            
        def ws_listener():
            """Thread function to listen for websocket messages."""
            while self.ws:
                try:
                    message = self.ws.recv()
                    if message:
                        # Parse and process the message
                        data = json.loads(message)
                        self._handle_ws_message(data)
                        # Also put in queue for external access
                        self.message_queue.put(data)
                except Exception as e:
                    unreal.log_error(f"Error in websocket listener: {e}")
                    break
                    
            unreal.log("WebSocket listener thread ended")
            
        # Create and start the thread
        self.ws_thread = threading.Thread(target=ws_listener)
        self.ws_thread.daemon = True
        self.ws_thread.start()
        unreal.log("Started WebSocket listener thread")
        
    def _handle_ws_message(self, message):
        """Handle messages received from the ComfyUI websocket.
        
        Args:
            message: The websocket message data
        """
        if "type" not in message:
            return
            
        msg_type = message["type"]
        data = message.get("data", {})
        
        if msg_type == "execution_start":
            prompt_id = data.get("prompt_id")
            unreal.log(f"Execution started for prompt: {prompt_id}")
            # Initialize status tracking for this prompt
            self.execution_status[prompt_id] = {
                "status": "running",
                "progress": 0,
                "current_node": None,
                "completed_nodes": [],
                "errors": [],
                "generation_id": self.generation_id  # Associate with current generation
            }
            
        elif msg_type == "executing":
            prompt_id = data.get("prompt_id")
            node_id = data.get("node")
            
            if prompt_id in self.execution_status:
                if node_id:
                    self.execution_status[prompt_id]["current_node"] = node_id
                    unreal.log(f"Executing node: {node_id}")
                else:
                    # None indicates execution complete
                    self.execution_status[prompt_id]["status"] = "completed"
                    self.execution_status[prompt_id]["current_node"] = None
                    unreal.log(f"Execution completed for prompt: {prompt_id}")
                    
        elif msg_type == "progress":
            prompt_id = data.get("prompt_id")
            node_id = data.get("node")
            value = data.get("value", 0)
            max_value = data.get("max", 100)
            
            if prompt_id in self.execution_status and max_value > 0:
                progress = int((value / max_value) * 100)
                self.execution_status[prompt_id]["progress"] = progress
                unreal.log(f"Progress on node {node_id}: {progress}%")
                
        elif msg_type == "execution_error":
            prompt_id = data.get("prompt_id")
            error_details = {
                "error_type": data.get("exception_type", "Unknown error"),
                "error_message": data.get("exception_message", "Unknown error message"),
                "node_id": data.get("node_id"),
                "traceback": data.get("traceback")
            }
            
            if prompt_id in self.execution_status:
                self.execution_status[prompt_id]["status"] = "error"
                self.execution_status[prompt_id]["errors"].append(error_details)
                
            error_msg = f"Error in prompt {prompt_id}"
            if error_details["node_id"]:
                error_msg += f", node {error_details['node_id']}"
            error_msg += f": {error_details['error_message']}"
            
            unreal.log_error(error_msg)
            
        elif msg_type == "executed":
            prompt_id = data.get("prompt_id")
            node_id = data.get("node")
            
            if prompt_id in self.execution_status and node_id:
                if node_id not in self.execution_status[prompt_id]["completed_nodes"]:
                    self.execution_status[prompt_id]["completed_nodes"].append(node_id)
                    
    def get_prompt_status(self, prompt_id):
        """Get the status of a prompt execution.
        
        Args:
            prompt_id: The ID of the prompt to check
            
        Returns:
            dict: Status information for the prompt
        """
        if prompt_id in self.execution_status:
            return self.execution_status[prompt_id]
        return {"status": "unknown", "progress": 0, "errors": []}

    def _make_request(self, method, url, **kwargs):
        """Make an HTTP request with error handling.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to request
            **kwargs: Additional arguments to pass to requests
            
        Returns:
            Response object
        """
        import requests
        try:
            response = requests.request(method, url, **kwargs)
            return response
        except Exception as e:
            # Better error messages for common issues
            error_msg = str(e)
            if "ConnectionError" in error_msg or "Connection refused" in error_msg:
                unreal.log_error(f"Could not connect to ComfyUI server at {self.server_url} - Is the server running?")
            elif "Timeout" in error_msg:
                unreal.log_error(f"Connection to ComfyUI server timed out - Server may be busy or unresponsive")
            else:
                unreal.log_error(f"HTTP request error ({method} {url}): {error_msg}")
            raise

    def generate_with_flux_workflow(self, prompt, negative_prompt="", width=1024, height=1024, output_dir=None):
        """Generate a texture using the FluxSchnell workflow.
        
        Args:
            prompt: Text description for the image
            negative_prompt: Text to avoid in the image
            width: Width of the output image
            height: Height of the output image
            output_dir: Directory to save the output (uses temp dir if None)
            
        Returns:
            str: Path to the generated texture file, or None on failure
        """
        import os
        import tempfile
        import uuid
        import time
        
        unreal.log("Generating texture with FluxSchnell workflow")
        unreal.log(f"Prompt: {prompt}")
        
        # Validate FluxSchnell requirements
        if not self.validate_flux_requirements():
            unreal.log_warning("FluxSchnell requirements not met, cannot generate with this workflow")
            return None
        
        # Set up output directory and filename
        if not output_dir:
            output_dir = tempfile.gettempdir()
        os.makedirs(output_dir, exist_ok=True)
        
        filename = f"dreamwave_flux_{uuid.uuid4().hex[:8]}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Create the workflow
        workflow = self.create_flux_workflow(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height
        )
        
        # Store reference to prompt_id for cleanup
        prompt_id = None
        
        try:
            # Ensure we have a websocket connection for status updates if available
            if WEBSOCKET_AVAILABLE:
                if not self.ws:
                    self.connect_websocket()
            
            # Queue the workflow
            unreal.log("Queuing FluxSchnell workflow")
            url = f"{self.server_url}/prompt"
            response = self._make_request('POST', url, json={"prompt": workflow, "client_id": self.client_id})
            
            if response.status_code != 200:
                unreal.log_error(f"Error queueing workflow: {response.status_code}")
                unreal.log_error(f"Response: {response.text}")
                return None
                
            prompt_id = response.json().get("prompt_id")
            if not prompt_id:
                unreal.log_error("No prompt ID returned")
                return None
                
            unreal.log(f"Workflow queued with prompt ID: {prompt_id}")
            
            # Associate this prompt_id with the current generation_id for tracking
            if self.generation_id and prompt_id in self.execution_status:
                self.execution_status[prompt_id]["generation_id"] = self.generation_id
            
            # Wait for execution to complete
            max_wait_time = 180  # seconds
            start_time = time.time()
            
            # Use websocket status tracking if available, otherwise use polling
            if self.ws and prompt_id in self.execution_status:
                unreal.log("Using websocket for real-time status updates")
                
                # Wait for completion or timeout
                while time.time() - start_time < max_wait_time:
                    status = self.get_prompt_status(prompt_id)
                    
                    # Check for completion
                    if status["status"] == "completed":
                        unreal.log("Execution completed via websocket notification")
                        break
                        
                    # Check for errors
                    if status["status"] == "error":
                        error_details = status["errors"][-1] if status["errors"] else {"error_message": "Unknown error"}
                        unreal.log_error(f"Execution error: {error_details['error_message']}")
                        return None
                        
                    # Print progress if available
                    if "progress" in status:
                        unreal.log(f"Progress: {status['progress']}%")
                        
                    # Sleep before checking again
                    time.sleep(1)
            else:
                # Fallback to polling if websocket not available
                unreal.log("Websocket not available, using polling for status updates")
                
                attempts = 0
                max_attempts = 60
                
                while attempts < max_attempts:
                    # Poll history API
                    history_url = f"{self.server_url}/history/{prompt_id}"
                    history_response = self._make_request('GET', history_url)
                    
                    if history_response.status_code == 200:
                        history_data = history_response.json()
                        
                        # Check if execution is complete (output exists)
                        if "outputs" in history_data and history_data["outputs"]:
                            unreal.log("Execution completed via polling")
                            break
                    
                    # Wait before polling again
                    time.sleep(3)
                    attempts += 1
                    
                    # Provide some feedback every few attempts
                    if attempts % 5 == 0:
                        unreal.log(f"Still waiting for execution... ({attempts}/{max_attempts})")
            
            # Fetch the results from history (regardless of whether websocket was used)
            unreal.log("Fetching results from history API")
            history_url = f"{self.server_url}/history/{prompt_id}"
            
            # Try a few times, as there might be a delay between completion and history update
            for _ in range(5):
                history_response = self._make_request('GET', history_url)
                
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    
                    # Check for outputs
                    if "outputs" in history_data:
                        # Look for image outputs
                        for node_id, node_output in history_data["outputs"].items():
                            if "images" in node_output:
                                for img_data in node_output["images"]:
                                    if "filename" in img_data:
                                        image_filename = img_data["filename"]
                                        unreal.log(f"Image generated: {image_filename}")
                                        
                                        # Download the image
                                        image_url = f"{self.server_url}/view?filename={image_filename}&subfolder=&type=temp"
                                        image_response = self._make_request('GET', image_url)
                                        
                                        if image_response.status_code == 200:
                                            # Save the image
                                            with open(output_path, "wb") as f:
                                                f.write(image_response.content)
                                            
                                            unreal.log(f"Image saved to: {output_path}")
                                            return output_path
                                        else:
                                            unreal.log_error(f"Error downloading image: {image_response.status_code}")
                                            
                # Sleep before trying again
                time.sleep(2)
            
            unreal.log_error(f"Timeout waiting for execution to complete or results not found")
            return None
            
        except Exception as e:
            unreal.log_error(f"Error generating with FluxSchnell workflow: {e}")
            import traceback
            traceback.print_exc()
            return None
            
        finally:
            # Clean up execution status data to avoid memory leaks
            if prompt_id and prompt_id in self.execution_status:
                del self.execution_status[prompt_id]

    def validate_flux_requirements(self):
        """Check if all required FluxSchnell model files are available.
        
        Returns:
            bool: True if all required models are available, False otherwise
        """
        required_models = {
            "flux1-schnell.safetensors": "models/unet/",
            "t5xxl_fp16.safetensors": "models/clip/",
            "clip_l.safetensors": "models/clip/",
            "ae.safetensors": "models/vae/"
        }
        
        missing_models = []
        
        try:
            # Query the ComfyUI API for available models
            model_list_url = f"{self.server_url}/model_list"
            response = self._make_request('GET', model_list_url)
            
            if response.status_code != 200:
                unreal.log_error(f"Error fetching model list: {response.status_code}")
                return False
                
            model_data = response.json()
            
            # Check each required model
            for model_file, model_path in required_models.items():
                category = model_path.split('/')[1]  # e.g., "unet", "clip", "vae"
                
                if category not in model_data:
                    missing_models.append(f"{model_path}{model_file}")
                    continue
                    
                if model_file not in model_data[category]:
                    missing_models.append(f"{model_path}{model_file}")
            
            if missing_models:
                unreal.log_warning("Missing required models for FluxSchnell workflow:")
                for model in missing_models:
                    unreal.log_warning(f"  - {model}")
                unreal.log_warning("Please download these files from: https://comfyanonymous.github.io/ComfyUI_examples/flux/")
                return False
                
            unreal.log("All required FluxSchnell models are available!")
            return True
            
        except Exception as e:
            unreal.log_error(f"Error validating FluxSchnell requirements: {e}")
            return False
            
    def create_flux_workflow(self, prompt, negative_prompt="", width=1024, height=1024, seed=None):
        """Create a workflow based on the FluxSchnell example.
        
        Args:
            prompt: Text description for the image
            negative_prompt: Text to avoid in the image
            width: Width of the output image
            height: Height of the output image
            seed: Random seed (will generate one if None)
            
        Returns:
            dict: A workflow structure ready to send to ComfyUI
        """
        if seed is None:
            import random
            seed = random.randint(1, 2147483647)
        
        # Create the workflow structure matching the FluxSchnell_workflow.json
        # This structure uses the exact node IDs and connections from that file
        workflow = {
            # Model loaders
            "10": {
                "inputs": {},
                "class_type": "VAELoader",
                "widgets_values": ["ae.safetensors"]
            },
            "11": {
                "inputs": {},
                "class_type": "DualCLIPLoader",
                "widgets_values": ["t5xxl_fp16.safetensors", "clip_l.safetensors", "flux", "default"]
            },
            "12": {
                "inputs": {},
                "class_type": "UNETLoader",
                "widgets_values": ["flux1-schnell.safetensors", "default"]
            },
            
            # Empty latent image
            "5": {
                "inputs": {},
                "class_type": "EmptyLatentImage",
                "widgets_values": [width, height, 1]
            },
            
            # Noise generation
            "25": {
                "inputs": {},
                "class_type": "RandomNoise",
                "widgets_values": [seed, "randomize"]
            },
            
            # Sampler setup
            "16": {
                "inputs": {},
                "class_type": "KSamplerSelect",
                "widgets_values": ["euler"]
            },
            
            # Text encoding for prompt
            "6": {
                "inputs": {
                    "clip": ["11", 0]
                },
                "class_type": "CLIPTextEncode",
                "widgets_values": [prompt]
            },
            
            # Scheduler - 4 steps as recommended for FluxSchnell
            "17": {
                "inputs": {
                    "model": ["12", 0]
                },
                "class_type": "BasicScheduler",
                "widgets_values": ["simple", 4, 1]
            },
            
            # Guider setup
            "22": {
                "inputs": {
                    "model": ["12", 0],
                    "conditioning": ["6", 0]
                },
                "class_type": "BasicGuider",
            },
            
            # Custom sampler for FluxSchnell
            "13": {
                "inputs": {
                    "noise": ["25", 0],
                    "guider": ["22", 0],
                    "sampler": ["16", 0],
                    "sigmas": ["17", 0],
                    "latent_image": ["5", 0]
                },
                "class_type": "SamplerCustomAdvanced",
            },
            
            # VAE Decode
            "8": {
                "inputs": {
                    "samples": ["13", 0],
                    "vae": ["10", 0]
                },
                "class_type": "VAEDecode",
            },
            
            # Save Image
            "9": {
                "inputs": {
                    "images": ["8", 0]
                },
                "class_type": "SaveImage",
                "widgets_values": ["dreamwave"]
            }
        }
        
        # Add all connections between nodes
        connections = [
            {"from": {"node": 11, "slot": 0}, "to": {"node": 6, "slot": 0}},  # CLIP to CLIPTextEncode
            {"from": {"node": 10, "slot": 0}, "to": {"node": 8, "slot": 1}},  # VAE to VAEDecode
            {"from": {"node": 16, "slot": 0}, "to": {"node": 13, "slot": 2}},  # KSamplerSelect to SamplerCustomAdvanced
            {"from": {"node": 17, "slot": 0}, "to": {"node": 13, "slot": 3}},  # BasicScheduler to SamplerCustomAdvanced
            {"from": {"node": 5, "slot": 0}, "to": {"node": 13, "slot": 4}},   # EmptyLatentImage to SamplerCustomAdvanced
            {"from": {"node": 13, "slot": 0}, "to": {"node": 8, "slot": 0}},   # SamplerCustomAdvanced to VAEDecode
            {"from": {"node": 22, "slot": 0}, "to": {"node": 13, "slot": 1}},  # BasicGuider to SamplerCustomAdvanced
            {"from": {"node": 25, "slot": 0}, "to": {"node": 13, "slot": 0}},  # RandomNoise to SamplerCustomAdvanced
            {"from": {"node": 12, "slot": 0}, "to": {"node": 17, "slot": 0}},  # UNETLoader to BasicScheduler
            {"from": {"node": 12, "slot": 0}, "to": {"node": 22, "slot": 0}},  # UNETLoader to BasicGuider
            {"from": {"node": 6, "slot": 0}, "to": {"node": 22, "slot": 1}},   # CLIPTextEncode to BasicGuider
            {"from": {"node": 8, "slot": 0}, "to": {"node": 9, "slot": 0}}     # VAEDecode to SaveImage
        ]
        
        # Normally for the ComfyUI API, we would just need to use the node definitions
        # But we'll return both the workflow and connections for reference
        return workflow

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