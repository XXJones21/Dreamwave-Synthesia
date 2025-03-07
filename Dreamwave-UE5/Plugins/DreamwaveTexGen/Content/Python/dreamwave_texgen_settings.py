"""
Dreamwave Texture Generator - Settings
This module contains settings for the Dreamwave Texture Generator.
"""

import os
import unreal

class Settings:
    """Settings for the Dreamwave Texture Generator."""
    
    def __init__(self):
        """Initialize default settings."""
        self.ComfyUIServerURL = "http://127.0.0.1:8188"
        
        # Path to ComfyUI installation - used for launching the server
        self.ComfyUIPath = ""  # Will be auto-detected if empty
        
        # Path to workflow file - if empty, will use built-in workflow
        self.WorkflowFilePath = ""
        
        # Output directory for generated textures
        # If empty, will use project's Content/DreamwaveTextures folder
        self.OutputDirectory = ""
        
        # Style presets for texture generation
        self.VaporwavePreset = "colorful, neon, retro, 80s, vaporwave, pastel colors, palm trees, grid"
        self.SynthwavePreset = "dark, neon, sci-fi, synthwave, purple, blue, cyber, retro futuristic"
        self.CyberpunkPreset = "cyberpunk, futuristic, high tech, neon lights, urban, dystopian, rainy"
        self.RetroPreset = "retro, vintage, old-school, pixelated, 8-bit, nostalgic"
        
        # Try to load settings from plugin directory
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from settings.json if it exists."""
        try:
            # Get the plugin dir
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            settings_path = os.path.join(plugin_dir, "settings.json")
            
            if os.path.exists(settings_path):
                import json
                with open(settings_path, "r") as f:
                    settings_data = json.load(f)
                
                # Apply settings from file
                for key, value in settings_data.items():
                    if hasattr(self, key):
                        setattr(self, key, value)
                
                unreal.log("Loaded settings from file")
            else:
                unreal.log("No settings file found, using defaults")
        except Exception as e:
            unreal.log_warning(f"Failed to load settings: {str(e)}")
    
    def save_settings(self):
        """Save settings to settings.json."""
        try:
            # Get the plugin dir
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            settings_path = os.path.join(plugin_dir, "settings.json")
            
            # Convert settings to dict
            settings_data = {
                key: value for key, value in self.__dict__.items()
                if not key.startswith("_")
            }
            
            # Save to file
            import json
            with open(settings_path, "w") as f:
                json.dump(settings_data, f, indent=4)
            
            unreal.log("Saved settings to file")
            return True
        except Exception as e:
            unreal.log_warning(f"Failed to save settings: {str(e)}")
            return False

# Create global settings instance
SETTINGS = Settings() 