"""
Dreamwave Command - A simple direct Python command to launch Dreamwave
"""

import unreal
import os
import sys

def run_dreamwave():
    """Run the Dreamwave Texture Generator UI."""
    try:
        unreal.log("Launching Dreamwave Texture Generator...")
        
        # Add plugin directory to path if needed
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
            
        # Import the required modules
        import dreamwave_texgen_api
        import dreamwave_texgen_ui
        
        # Create API and run UI
        api = dreamwave_texgen_api.DreamwaveTexGenAPI()
        dreamwave_texgen_ui.show_ui(api)
        
        return True
    except Exception as e:
        unreal.log_error(f"Failed to launch Dreamwave: {str(e)}")
        try:
            unreal.EditorDialog.show_message(
                title="Dreamwave Error",
                message=f"Failed to launch Dreamwave: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except:
            unreal.log_error(f"Failed to show error dialog: {str(e)}")
        
        return False

def check_comfyui():
    """Check the status of the ComfyUI server."""
    try:
        unreal.log("Checking ComfyUI server status...")
        
        # Add plugin directory to path if needed
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
            
        # Import and run the status check
        import dreamwave_texgen_ui
        dreamwave_texgen_ui.check_comfyui_status()
        
        return True
    except Exception as e:
        unreal.log_error(f"Failed to check ComfyUI status: {str(e)}")
        return False

def launch_comfyui():
    """Launch the ComfyUI server."""
    try:
        unreal.log("Launching ComfyUI server...")
        
        # Add plugin directory to path if needed
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
            
        # Import and launch the server
        import dreamwave_texgen_ui
        dreamwave_texgen_ui.launch_comfyui_server()
        
        return True
    except Exception as e:
        unreal.log_error(f"Failed to launch ComfyUI server: {str(e)}")
        return False

# Print instructions when this module is imported directly
unreal.log("=== Dreamwave Commands ===")
unreal.log("- Type dreamwave_command.run_dreamwave() to open the Texture Generator UI")
unreal.log("- Type dreamwave_command.check_comfyui() to check the ComfyUI server status")
unreal.log("- Type dreamwave_command.launch_comfyui() to launch the ComfyUI server")

# For direct imports
if __name__ == "__main__":
    run_dreamwave() 