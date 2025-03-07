"""
Dreamwave Texture Generator Python Package
"""

# Use absolute imports instead of relative imports
import os
import sys
import unreal

# Make sure the current directory is in the Python path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)
    unreal.log(f"Added {plugin_dir} to Python path")

# Define a function to safely import modules
def import_modules():
    """Import the required modules."""
    try:
        # Import modules directly
        import dreamwave_texgen_api
        import dreamwave_texgen_ui
        import dreamwave_texgen_settings
        
        # Make them available from this package
        globals()['dreamwave_texgen_api'] = dreamwave_texgen_api
        globals()['dreamwave_texgen_ui'] = dreamwave_texgen_ui
        globals()['dreamwave_texgen_settings'] = dreamwave_texgen_settings
        
        # Also make the classes available
        globals()['DreamwaveTexGenAPI'] = dreamwave_texgen_api.DreamwaveTexGenAPI
        globals()['SETTINGS'] = dreamwave_texgen_settings.SETTINGS
        
        return True
    except Exception as e:
        unreal.log_error(f"Failed to import modules: {str(e)}")
        return False

# Direct function to open the UI
def open_ui():
    """Open the Dreamwave Texture Generator UI."""
    try:
        if import_modules():
            api = dreamwave_texgen_api.DreamwaveTexGenAPI()
            dreamwave_texgen_ui.show_ui(api)
            return True
        else:
            unreal.log_error("Failed to import required modules")
            return False
    except Exception as e:
        unreal.log_error(f"Failed to open UI: {str(e)}")
        return False

# When run directly, try to open the UI
if __name__ == "__main__":
    unreal.log("Running Dreamwave Texture Generator package directly")
    if import_modules():
        unreal.log("Successfully imported modules")
        open_ui()
    else:
        unreal.log_error("Failed to import required modules") 