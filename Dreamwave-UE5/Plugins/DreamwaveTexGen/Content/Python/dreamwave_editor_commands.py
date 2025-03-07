"""
Dreamwave Texture Generator - Editor Commands
This module registers editor commands for the Dreamwave Texture Generator.
"""

import unreal
import os
import sys
import traceback

class DreamwaveEditorCommands:
    """Editor commands for Dreamwave that work with UE 5.5.3."""
    
    @staticmethod
    def open_texture_generator():
        """Open the Dreamwave Texture Generator interface."""
        try:
            # Get the plugin's Python directory
            plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if plugin_dir not in sys.path:
                sys.path.append(plugin_dir)
            
            # Import the API and UI modules
            from dreamwave_texgen_api import DreamwaveTexGenAPI
            import dreamwave_texgen_ui
            
            # Create the API and show the UI
            api = DreamwaveTexGenAPI()
            dreamwave_texgen_ui.show_ui(api)
            
            unreal.log("Dreamwave Texture Generator UI opened")
            return True
        except Exception as e:
            unreal.log_error(f"Failed to open Texture Generator: {str(e)}")
            unreal.log_error(f"Traceback: {traceback.format_exc()}")
            
            # Show error dialog with fallback
            try:
                unreal.EditorDialog.show_message(
                    title="Dreamwave Texture Generator Error",
                    message=f"Error: {str(e)}\n\nPlease check the Output Log for details.",
                    message_type=unreal.AppMsgType.OK
                )
            except:
                print(f"ERROR: Failed to open Texture Generator: {str(e)}")
            
            return False

# Add a register_command function that can be called from init_unreal.py
def register_command(command_name, command_script, description):
    """Register a Python command using an approach compatible with UE 5.5.3."""
    try:
        # Try to register the command in the global Python namespace
        global_dict = {}
        exec(f"""
def _execute_{command_name}():
    {command_script}
""", global_dict)
        
        # Store the function in the module namespace
        globals()[f"_execute_{command_name}"] = global_dict[f"_execute_{command_name}"]
        
        # Log successful registration
        unreal.log(f"Registered '{command_name}' command using compatible approach")
        return True
    except Exception as e:
        unreal.log_error(f"Failed to register '{command_name}' command: {str(e)}")
        return False

# Compatibility function to execute a registered command
def execute_command(command_name):
    """Execute a registered command by name."""
    try:
        # Look for the function in the global namespace
        func_name = f"_execute_{command_name}"
        if func_name in globals():
            globals()[func_name]()
            return True
        else:
            unreal.log_error(f"Command '{command_name}' not found")
            return False
    except Exception as e:
        unreal.log_error(f"Failed to execute command '{command_name}': {str(e)}")
        return False

# Register the commands using a compatible approach
try:
    # Register the open_texture_generator function directly without relying on PythonBPLib
    unreal.log("Registering Dreamwave Editor Commands...")
    
    # Add to the global Python commands for direct call
    globals()["open_dreamwave_texture_generator"] = DreamwaveEditorCommands.open_texture_generator
    
    unreal.log("Dreamwave Editor Commands registered successfully")
except Exception as e:
    unreal.log_error(f"Failed to register Dreamwave Editor Commands: {str(e)}")
    unreal.log_error(f"Traceback: {traceback.format_exc()}") 