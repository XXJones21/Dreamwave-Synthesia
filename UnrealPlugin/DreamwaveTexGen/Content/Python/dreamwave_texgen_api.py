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

# Add necessary paths to import our Python bridge
script_dir = os.path.dirname(os.path.abspath(__file__))
dreamwave_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))), "dreamwave")
sys.path.append(dreamwave_dir)

try:
    from texture_gen.comfy_bridge import ComfyBridge
except ImportError:
    unreal.log_error("Failed to import ComfyBridge. Check that the dreamwave Python package is installed correctly.")
    raise

class DreamwaveTexGenAPI:
    """API for generating textures from within Unreal Engine."""
    
    def __init__(self):
        """Initialize the API."""
        self.settings = unreal.get_default_object(unreal.load_class(None, '/Script/DreamwaveTexGen.DreamwaveTexGenSettings'))
        self.bridge = None
        self.initialize_bridge()
    
    def initialize_bridge(self):
        """Initialize the ComfyUI bridge using plugin settings."""
        server_url = self.settings.ComfyUIServerURL
        if not server_url or server_url == "":
            server_url = "http://127.0.0.1:8188"
        
        unreal.log(f"Initializing ComfyUI bridge with server URL: {server_url}")
        self.bridge = ComfyBridge(server_address=server_url)
    
    def get_workflow_path(self):
        """Get the path to the ComfyUI workflow file from settings."""
        workflow_path = self.settings.WorkflowFilePath.FilePath
        
        if not workflow_path or workflow_path == "":
            # Try to use the default workflow from the project
            project_workflow = os.path.join(dreamwave_dir, "..", "ComfyUI", "FluxSchnell_workflow.json")
            if os.path.exists(project_workflow):
                return project_workflow
            raise ValueError("No workflow file specified in settings and default workflow not found.")
        
        return workflow_path
    
    def get_output_directory(self):
        """Get the output directory for generated textures."""
        output_path = self.settings.DefaultOutputDirectory.Path
        
        if not output_path or output_path == "":
            # Use a temp directory as fallback
            output_path = os.path.join(tempfile.gettempdir(), "DreamwaveTexGen")
            os.makedirs(output_path, exist_ok=True)
        else:
            # Convert relative game content path to absolute path
            game_content_dir = unreal.Paths.project_content_dir()
            absolute_path = os.path.join(game_content_dir, output_path)
            output_path = absolute_path
            os.makedirs(output_path, exist_ok=True)
        
        return output_path
    
    def generate_texture(self, prompt, style_presets=None):
        """Generate a texture from a text prompt.
        
        Args:
            prompt: Text description of the texture to generate
            style_presets: Optional list of style presets to apply
            
        Returns:
            Path to the generated texture file
        """
        if not self.bridge:
            self.initialize_bridge()
        
        # Apply style presets if provided
        full_prompt = prompt
        if style_presets:
            preset_text = ", ".join(style_presets)
            full_prompt = f"{prompt}, {preset_text}"
        
        unreal.log(f"Generating texture with prompt: {full_prompt}")
        
        # Generate the texture
        try:
            texture_path = self.bridge.generate_texture(
                prompt=full_prompt,
                output_dir=self.get_output_directory(),
                workflow_path=self.get_workflow_path()
            )
            
            unreal.log(f"Texture generated successfully: {texture_path}")
            return texture_path
            
        except Exception as e:
            unreal.log_error(f"Error generating texture: {str(e)}")
            raise
    
    def import_texture_to_unreal(self, texture_path, asset_name=None, asset_path=None):
        """Import a generated texture into Unreal Engine.
        
        Args:
            texture_path: Path to the texture file
            asset_name: Name for the imported asset (or None to use the filename)
            asset_path: Path in the content browser (or None to use the default output directory)
            
        Returns:
            UTexture2D asset
        """
        if not os.path.exists(texture_path):
            raise ValueError(f"Texture file not found: {texture_path}")
        
        # Determine asset name and path
        if not asset_name:
            asset_name = os.path.splitext(os.path.basename(texture_path))[0]
        
        if not asset_path:
            rel_path = self.settings.DefaultOutputDirectory.Path
            if not rel_path or rel_path == "":
                rel_path = "Textures/Generated"
            
            asset_path = f"/Game/{rel_path}"
        
        # Make sure to append the asset name to the path
        full_asset_path = f"{asset_path}/{asset_name}"
        
        # Set import options
        import_options = unreal.TextureImportOptions()
        import_options.set_editor_property("compression_settings", unreal.TextureCompressionSettings.DEFAULT)
        import_options.set_editor_property("srgb", True)
        
        # Import the texture
        task = unreal.AssetImportTask()
        task.set_editor_property("automated", True)
        task.set_editor_property("destination_path", asset_path)
        task.set_editor_property("destination_name", asset_name)
        task.set_editor_property("filename", texture_path)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        
        # Get the imported asset
        imported_asset = unreal.EditorAssetLibrary.find_asset_data(full_asset_path).get_asset()
        
        if imported_asset:
            unreal.log(f"Texture imported successfully: {full_asset_path}")
            return imported_asset
        else:
            unreal.log_error(f"Failed to import texture: {texture_path}")
            return None
    
    def generate_and_import(self, prompt, style_presets=None, asset_name=None, asset_path=None):
        """Generate a texture and import it into Unreal Engine.
        
        Args:
            prompt: Text description of the texture to generate
            style_presets: Optional list of style presets to apply
            asset_name: Name for the imported asset (or None to use a generated name)
            asset_path: Path in the content browser (or None to use the default output directory)
            
        Returns:
            UTexture2D asset
        """
        texture_path = self.generate_texture(prompt, style_presets)
        
        # Generate asset name if not provided
        if not asset_name:
            # Create a clean asset name from the prompt (first few words)
            clean_name = "".join(x for x in prompt if x.isalnum() or x.isspace()).strip()
            words = clean_name.split()
            if len(words) > 3:
                words = words[:3]
            asset_name = "T_" + "_".join(words)
        
        # Import the texture
        return self.import_texture_to_unreal(texture_path, asset_name, asset_path)

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