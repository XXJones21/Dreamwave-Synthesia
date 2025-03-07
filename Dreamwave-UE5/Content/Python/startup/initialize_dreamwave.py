"""
Dreamwave Texture Generator Initialization Script
This script can be run manually from the Python console to initialize the plugin.
"""

import unreal
import os
import sys
import importlib

def init_dreamwave():
    """Initialize the Dreamwave Texture Generator plugin manually."""
    # Print startup message
    unreal.log("Manually initializing Dreamwave Texture Generator plugin...")
    
    # Add plugin path to sys.path
    plugin_path = os.path.join(unreal.Paths.project_plugins_dir(), "DreamwaveTexGen", "Content", "Python")
    if plugin_path not in sys.path:
        sys.path.append(plugin_path)
        unreal.log(f"Added plugin path to sys.path: {plugin_path}")
    
    # Try to import the initialization module
    try:
        # Try to import the init module
        import init_unreal
        importlib.reload(init_unreal)  # Reload in case it was imported before
        
        # Call the manual initialization function
        result = init_unreal.manual_init()
        unreal.log(result)
        
        return "Dreamwave Texture Generator initialized successfully. Look for the Dreamwave menu in the main toolbar."
    except Exception as e:
        error_msg = f"Failed to initialize Dreamwave Texture Generator: {str(e)}"
        unreal.log_error(error_msg)
        return error_msg

# Run the initialization function automatically
result = init_dreamwave()
print(result) 