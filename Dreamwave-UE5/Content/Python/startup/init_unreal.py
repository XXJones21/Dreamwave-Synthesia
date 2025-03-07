"""
Dreamwave Texture Generator - Initialization Script
This script runs when Unreal Engine starts and initializes the texture generator UI.
"""

import unreal
import os
import sys

# Add our plugin's Python directory to the path for imports
plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(plugin_dir)

from dreamwave_texgen_api import DreamwaveTexGenAPI

# Global reference to our API
DREAMWAVE_API = None

def register_menu():
    """Register the Dreamwave Texture Generator menu in the Unreal Editor."""
    menus = unreal.ToolMenus.get()
    main_menu = menus.find_menu("LevelEditor.MainMenu")
    
    if main_menu:
        # Create Dreamwave menu entry
        dreamwave_menu = main_menu.add_sub_menu(
            "DreamwaveMenu", "Dreamwave", "Dreamwave Tools", "Dreamwave Tools"
        )
        
        # Add texture generator entry
        section = dreamwave_menu.add_section("TextureGenSection", "Texture Generator")
        entry = unreal.ToolMenuEntry(
            name="OpenTexGen",
            label="Open Texture Generator",
            tool_tip="Open the Dreamwave Texture Generator interface"
        )
        entry.set_script_delegate(unreal.ToolMenuStringDelegate(lambda: open_texture_generator()))
        section.add_menu_entry("GenerateTextures", entry)
    
    # Apply all menu changes
    menus.refresh_all_widgets()

def open_texture_generator():
    """Open the texture generator UI."""
    global DREAMWAVE_API
    
    try:
        # Initialize the API if not already done
        if DREAMWAVE_API is None:
            DREAMWAVE_API = DreamwaveTexGenAPI()
            
        # Import our UI module lazily
        import dreamwave_texgen_ui
        dreamwave_texgen_ui.show_ui(DREAMWAVE_API)
        
        unreal.log("Dreamwave Texture Generator UI opened")
    except Exception as e:
        unreal.log_error(f"Failed to open Texture Generator: {str(e)}")
        unreal.log_warning("Make sure ComfyUI is running and the dreamwave package is installed")

# Register the startup callback to initialize after Unreal Engine is fully loaded
unreal.register_python_startup_callback(lambda: register_menu()) 