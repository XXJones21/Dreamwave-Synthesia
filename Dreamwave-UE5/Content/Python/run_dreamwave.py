"""
Simple script to run the Dreamwave Texture Generator.
Execute this in the Python console to open the Texture Generator.

Instructions:
1. Import this module: import run_dreamwave
2. Run the function: run_dreamwave.run_dreamwave()
"""

import unreal
import sys
import os
import traceback

def run_dreamwave():
    """Open the Dreamwave Texture Generator UI."""
    try:
        unreal.log("Starting Dreamwave Texture Generator...")
        
        # Find the plugin path
        plugin_dir = os.path.join(unreal.Paths.project_plugins_dir(), "DreamwaveTexGen", "Content", "Python")
        
        # Add to path if needed
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
            unreal.log(f"Added {plugin_dir} to sys.path")
        
        # Import modules
        try:
            import dreamwave_texgen_api
            import dreamwave_texgen_ui
            
            # Create API and show UI
            api = dreamwave_texgen_api.DreamwaveTexGenAPI()
            dreamwave_texgen_ui.show_ui(api)
            
            unreal.log("Dreamwave Texture Generator opened successfully")
            return "Dreamwave Texture Generator opened successfully"
        except ImportError as import_err:
            error_msg = f"Import Error: {str(import_err)}\nTrace: {traceback.format_exc()}"
            unreal.log_error(error_msg)
            
            # Show error dialog
            unreal.EditorDialog.show_message(
                title="Dreamwave Texture Generator Error",
                message=f"Failed to import required modules:\n{str(import_err)}\n\nCheck the Output Log for details.",
                dialog_type=unreal.AppMsgType.OK
            )
            
            return error_msg
    except Exception as e:
        error_msg = f"Error: {str(e)}\nTrace: {traceback.format_exc()}"
        unreal.log_error(error_msg)
        
        # Show error dialog
        unreal.EditorDialog.show_message(
            title="Dreamwave Texture Generator Error",
            message=f"Failed to open Dreamwave Texture Generator:\n{str(e)}",
            dialog_type=unreal.AppMsgType.OK
        )
        
        return error_msg

# Don't auto-run when imported - requires explicit function call
print("To open Dreamwave Texture Generator, run: run_dreamwave.run_dreamwave()") 