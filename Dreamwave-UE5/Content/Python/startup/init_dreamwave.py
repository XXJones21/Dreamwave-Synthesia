"""
Dreamwave Texture Generator Initialization Script
This script can be run manually from the Python console to initialize the plugin.
"""

import unreal
import os
import sys
import importlib
import traceback

def init_dreamwave():
    """Initialize the Dreamwave Texture Generator plugin manually."""
    # Print startup message
    unreal.log("Manually initializing Dreamwave Texture Generator plugin...")
    
    try:
        # Add plugin path to sys.path
        plugin_path = os.path.join(unreal.Paths.project_plugins_dir(), "DreamwaveTexGen", "Content", "Python")
        if plugin_path not in sys.path:
            sys.path.append(plugin_path)
            unreal.log(f"Added plugin path to sys.path: {plugin_path}")
        
        # Add editor utility path to sys.path
        utility_path = os.path.join(unreal.Paths.project_content_dir(), "Python", "EditorUtility")
        if utility_path not in sys.path:
            sys.path.append(utility_path)
            unreal.log(f"Added editor utility path to sys.path: {utility_path}")
        
        # Don't try to create the utility widget automatically at startup
        # This will be done manually by the user later if needed
        """
        try:
            import dreamwave_texgen_widget
            dreamwave_texgen_widget.register_editor_utility_tab()
            unreal.log("Created Editor Utility Widget for Dreamwave Texture Generator")
        except Exception as e:
            unreal.log_error(f"Failed to create Editor Utility Widget: {str(e)}")
        """
        
        # Try to import the initialization module - don't try to reload it
        # as reloading can sometimes cause issues
        try:
            # Import manually but don't reload
            plugin_init_path = os.path.join(plugin_path, "init_unreal.py")
            if os.path.exists(plugin_init_path):
                unreal.log(f"Loading plugin initialization from {plugin_init_path}")
                
                # Don't use importlib.reload here to avoid potential issues
                if "init_unreal" not in sys.modules:
                    import init_unreal
                    # Call manually without reloading
                    if hasattr(init_unreal, 'manual_init'):
                        result = init_unreal.manual_init()
                        unreal.log(result)
                else:
                    unreal.log("Initialization module already loaded, not reloading to avoid issues")
            else:
                unreal.log_warning(f"Plugin initialization script not found at {plugin_init_path}")
            
            return "Dreamwave Texture Generator initialized successfully. Use Python console to run: import run_dreamwave"
        except Exception as e:
            error_msg = f"Failed to initialize Dreamwave Texture Generator: {str(e)}"
            unreal.log_error(error_msg)
            unreal.log_error(traceback.format_exc())
            return error_msg
    except Exception as outer_e:
        error_msg = f"Failed to set up paths for Dreamwave Texture Generator: {str(outer_e)}"
        unreal.log_error(error_msg)
        unreal.log_error(traceback.format_exc())
        return error_msg

# Don't run the initialization automatically at import time
# This prevents any potential issues during project load
# Instead, print a message telling the user how to init manually
print("To initialize Dreamwave Texture Generator, run: init_dreamwave() from this module") 