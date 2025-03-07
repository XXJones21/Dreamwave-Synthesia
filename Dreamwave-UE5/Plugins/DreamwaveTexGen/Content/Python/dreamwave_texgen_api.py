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