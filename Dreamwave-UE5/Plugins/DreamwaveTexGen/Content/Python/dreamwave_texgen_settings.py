"""
Dreamwave Texture Generator - Settings Module
Provides settings management for the texture generator.
"""

import unreal
import os
import json

class DreamwaveTexGenSettings:
    """Settings for the Dreamwave Texture Generator plugin."""
    
    def __init__(self):
        """Initialize with default values."""
        # ComfyUI server URL
        self.ComfyUIServerURL = "http://127.0.0.1:8188"
        
        # Workflow file path and output directory
        self.WorkflowFilePath = None
        self.OutputDirectory = None
        
        # Load settings from file if available
        self.load_settings()
        
        # Set default style presets if not loaded
        if not hasattr(self, 'VaporwavePreset') or not self.VaporwavePreset:
            self.VaporwavePreset = "colorful, neon, retro, 80s, vaporwave, pastel colors, palm trees, grid"
        
        if not hasattr(self, 'SynthwavePreset') or not self.SynthwavePreset:
            self.SynthwavePreset = "dark, neon, sci-fi, synthwave, purple, blue, cyber, retro futuristic"
        
        if not hasattr(self, 'CyberpunkPreset') or not self.CyberpunkPreset:
            self.CyberpunkPreset = "cyberpunk, futuristic, high tech, neon lights, urban, dystopian, rainy"
        
        if not hasattr(self, 'RetroPreset') or not self.RetroPreset:
            self.RetroPreset = "retro, vintage, old-school, pixelated, 8-bit, nostalgic"
    
    def load_settings(self):
        """Load settings from a JSON file."""
        try:
            # Define settings file path in plugin directory
            plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            settings_file = os.path.join(plugin_dir, "Config", "DreamwaveTexGenSettings.json")
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                    
                    # Apply loaded settings to this instance
                    for key, value in settings.items():
                        setattr(self, key, value)
                        
                unreal.log(f"Loaded settings from {settings_file}")
            else:
                unreal.log("No settings file found, using defaults")
        except Exception as e:
            unreal.log_warning(f"Failed to load settings: {e}")
    
    def save_settings(self):
        """Save settings to a JSON file."""
        try:
            # Define settings file path in plugin directory
            plugin_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            config_dir = os.path.join(plugin_dir, "Config")
            
            # Create Config directory if it doesn't exist
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            settings_file = os.path.join(config_dir, "DreamwaveTexGenSettings.json")
            
            # Create a dictionary of settings
            settings = {
                "ComfyUIServerURL": self.ComfyUIServerURL,
                "VaporwavePreset": self.VaporwavePreset,
                "SynthwavePreset": self.SynthwavePreset,
                "CyberpunkPreset": self.CyberpunkPreset,
                "RetroPreset": self.RetroPreset
            }
            
            # Add file paths if they exist
            if hasattr(self, 'WorkflowFilePath') and self.WorkflowFilePath:
                settings["WorkflowFilePath"] = self.WorkflowFilePath
                
            if hasattr(self, 'OutputDirectory') and self.OutputDirectory:
                settings["OutputDirectory"] = self.OutputDirectory
            
            # Save settings to file
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
                
            unreal.log(f"Saved settings to {settings_file}")
            return True
        except Exception as e:
            unreal.log_error(f"Failed to save settings: {e}")
            return False
    
    def get_workflow_path(self):
        """Get the workflow file path."""
        return self.WorkflowFilePath
    
    def set_workflow_path(self, path):
        """Set the workflow file path."""
        self.WorkflowFilePath = path
        self.save_settings()
    
    def get_output_directory(self):
        """Get the output directory."""
        return self.OutputDirectory
    
    def set_output_directory(self, directory):
        """Set the output directory."""
        self.OutputDirectory = directory
        self.save_settings()

# Create a global instance
SETTINGS = DreamwaveTexGenSettings() 