"""
Dreamwave Texture Generator - Python Package Initialization
"""

import unreal
import os
import sys

def initialize_plugin():
    """Initialize the Dreamwave Texture Generator plugin."""
    try:
        unreal.log("Dreamwave Texture Generator plugin initializing...")
        
        # Add plugin directory to Python path
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
            unreal.log(f"Added plugin directory to Python path: {plugin_dir}")
        
        # Import and run initialization module
        try:
            import init_unreal
            unreal.log("Imported init_unreal module")
            
            # Register menu
            if hasattr(init_unreal, 'register_menu'):
                if init_unreal.register_menu():
                    unreal.log("Successfully registered Dreamwave menu")
                else:
                    unreal.log_warning("Failed to register Dreamwave menu")
                
            # Register command
            if hasattr(init_unreal, 'register_dreamwave_command'):
                if init_unreal.register_dreamwave_command():
                    unreal.log("Successfully registered Dreamwave command")
                else:
                    unreal.log_warning("Failed to register Dreamwave command")
                
            unreal.log("Dreamwave Texture Generator plugin initialized")
            return True
        except Exception as init_err:
            unreal.log_error(f"Failed to initialize Dreamwave plugin: {str(init_err)}")
            return False
    except Exception as e:
        unreal.log_error(f"Error in Dreamwave plugin initialization: {str(e)}")
        return False

# Initialize the plugin when the module is imported
initialize_plugin()

# Export useful functions
try:
    from dreamwave_texgen_ui import open_texture_generator_ui
    from dreamwave_texgen_ui import launch_comfyui_server
    from dreamwave_texgen_ui import check_comfyui_status
    
    # Make the most important functions available at package level
    __all__ = [
        'open_texture_generator_ui',
        'launch_comfyui_server',
        'check_comfyui_status'
    ]
except Exception as export_err:
    unreal.log_warning(f"Could not export all Dreamwave functions: {str(export_err)}")
    __all__ = [] 