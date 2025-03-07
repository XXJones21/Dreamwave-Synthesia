"""
Direct script to open the Dreamwave Texture Generator. 
Run this in the Unreal Engine console with:
py "D:/Tools/Dreamwave-Synthesia/Dreamwave-UE5/Content/Python/open_dreamwave.py"
"""

import unreal
import os
import sys
import traceback

# Set up required paths
try:
    # Get plugin path
    plugin_dir = os.path.join(unreal.Paths.project_plugins_dir(), "DreamwaveTexGen", "Content", "Python")
    
    # Add to path if not already there
    if plugin_dir not in sys.path:
        sys.path.append(plugin_dir)
        unreal.log(f"Added plugin dir to path: {plugin_dir}")
        
    # Verify the plugin path exists
    if not os.path.exists(plugin_dir):
        unreal.log_error(f"Plugin path does not exist: {plugin_dir}")
        unreal.EditorDialog.show_message(
            title="Error", 
            message=f"Plugin path not found: {plugin_dir}", 
            dialog_type=unreal.AppMsgType.OK
        )
        sys.exit(1)
    
    # Try to run the UI
    try:
        # First try importing the UI module
        unreal.log("Importing plugin modules...")
        import dreamwave_texgen_api
        import dreamwave_texgen_ui
        
        # Create API and show UI
        unreal.log("Creating API and showing UI...")
        api = dreamwave_texgen_api.DreamwaveTexGenAPI()
        dreamwave_texgen_ui.show_ui(api)
        
        unreal.log("Dreamwave Texture Generator opened successfully")
        
    except ImportError as ie:
        unreal.log_error(f"Import error: {str(ie)}")
        unreal.log_error(f"Traceback: {traceback.format_exc()}")
        
        # Try executing the script directly as fallback
        unreal.log("Falling back to direct script execution...")
        run_ui_path = os.path.join(plugin_dir, "run_ui.py")
        
        if os.path.exists(run_ui_path):
            unreal.log(f"Executing {run_ui_path}")
            try:
                with open(run_ui_path, 'r') as f:
                    script_content = f.read()
                    exec(script_content)
                    unreal.log("Script executed successfully")
            except Exception as exec_err:
                unreal.log_error(f"Failed to execute script: {str(exec_err)}")
                unreal.EditorDialog.show_message(
                    title="Script Execution Error",
                    message=f"Failed to execute UI script: {str(exec_err)}",
                    dialog_type=unreal.AppMsgType.OK
                )
        else:
            unreal.log_error(f"Script not found: {run_ui_path}")
            unreal.EditorDialog.show_message(
                title="File Not Found",
                message=f"UI script not found at: {run_ui_path}",
                dialog_type=unreal.AppMsgType.OK
            )
            
except Exception as e:
    unreal.log_error(f"Failed to open Dreamwave Texture Generator: {str(e)}")
    unreal.log_error(f"Traceback: {traceback.format_exc()}")
    unreal.EditorDialog.show_message(
        title="Dreamwave Error",
        message=f"Failed to open Dreamwave Texture Generator:\n{str(e)}",
        dialog_type=unreal.AppMsgType.OK
    ) 