"""
Dreamwave Texture Generator - UI Module
Provides a UI for the texture generator in Unreal Engine.
"""

import unreal
import os
import sys
import webbrowser
from functools import partial

def show_ui(api):
    """Show the texture generator UI window."""
    # Create a simple dialog window instead of using SWindow
    unreal.log("Opening Dreamwave Texture Generator UI...")
    
    # Try different UI approaches
    try:
        # First try: Editor Utility Widget fallback
        try:
            # Try to create an editor utility widget if possible
            utility_subsystem = unreal.EditorUtilitySubsystem.get_default_object()
            if utility_subsystem:
                unreal.log("Using EditorUtilitySubsystem to display UI")
                
                # Check if we have a valid blueprint path
                blueprint_path = "/Game/DreamwaveTexGen/UI/BP_DreamwaveTexGenUI.BP_DreamwaveTexGenUI"
                
                # Attempt to find the asset
                if unreal.EditorAssetLibrary.does_asset_exist(blueprint_path):
                    # Try to spawn the widget
                    widget = utility_subsystem.spawn_and_register_tab(unreal.load_asset(blueprint_path))
                    if widget:
                        unreal.log("Successfully opened UI through blueprint")
                        return widget
                    else:
                        unreal.log_warning("Failed to spawn widget from blueprint")
                else:
                    unreal.log_warning(f"Blueprint not found: {blueprint_path}")
        except Exception as blueprint_err:
            unreal.log_warning(f"Blueprint UI error: {str(blueprint_err)}")
        
        # Second try: Python-based UI as a fallback
        try:
            # Use the console dialog approach - most compatible
            return _show_generator_dialog(api)
        except Exception as dialog_err:
            unreal.log_warning(f"Dialog UI error: {str(dialog_err)}")
        
        # Third try: Console interface as last resort
        try:
            # If the UI fails, try a console-based interface
            return _console_interface(api)
        except Exception as console_err:
            unreal.log_error(f"Console UI error: {str(console_err)}")
            
        # Final fallback: Show an error message
        unreal.log_error("All UI approaches failed")
        
        try:
            # Try to use standard dialog library first
            if hasattr(unreal, 'EditorDialog'):
                unreal.EditorDialog.show_message(
                    title="Dreamwave Error",
                    message=f"Failed to open UI: {str(e)}",
                    message_type=unreal.AppMsgType.OK
                )
            elif hasattr(unreal, 'EditorDialogLibrary'):
                unreal.EditorDialogLibrary.show_message(
                    title="Dreamwave Error", 
                    message=f"Failed to open UI: {str(e)}",
                    dialog_type=unreal.AppMsgType.OK
                )
            else:
                unreal.log_warning("Could not use dialog library: module 'unreal' has no attribute 'EditorDialogLibrarySubsystem'")
                print(f"ERROR: Failed to open UI: {str(e)}")
        except Exception as dialog_err:
            unreal.log_error(f"Dialog UI error: {str(dialog_err)}")
            
    except Exception as e:
        unreal.log_error(f"Failed to show UI: {str(e)}")
        
        try:
            # Show error dialog with correct parameters
            unreal.EditorDialog.show_message(
                title="Dreamwave Error",
                message=f"Failed to open UI: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except:
            unreal.log_error(f"UI initialization error: {str(e)}")
            
    return None

def _show_generator_dialog(api):
    """Show a simple dialog for texture generation."""
    try:
        # Create the most basic UI possible
        title = "Dreamwave Texture Generator"
        prompt_message = "Enter a prompt to generate a texture:"
        
        # Try different dialog approaches
        user_prompt = None
        
        # First try: use the modern dialog system if available
        try:
            if hasattr(unreal, 'EditorDialog') and hasattr(unreal.EditorDialog, 'prompt_for_input'):
                result, user_prompt = unreal.EditorDialog.prompt_for_input(
                    title=title,
                    prompt=prompt_message
                )
                if not result or not user_prompt:
                    return None
        except Exception as input_err:
            unreal.log_warning(f"Could not use modern dialog: {str(input_err)}")
        
        # Second try: use an older EditorDialogLibrary if available
        if user_prompt is None:
            try:
                dialog_lib = unreal.get_engine_subsystem(unreal.EditorDialogLibrarySubsystem)
                if dialog_lib and hasattr(dialog_lib, 'prompt_for_input'):
                    result, user_prompt = dialog_lib.prompt_for_input(
                        title=title,
                        prompt=prompt_message
                    )
                    if not result or not user_prompt:
                        return None
            except Exception as lib_err:
                unreal.log_warning(f"Could not use dialog library: {str(lib_err)}")
        
        # Third try: create a simple message dialog
        if user_prompt is None:
            try:
                # Show a simple message dialog for input
                dialog_result = unreal.EditorDialog.show_message(
                    title=title,
                    message=prompt_message,
                    message_type=unreal.AppMsgType.OK_CANCEL
                )
                
                # If user clicked OK, use a default prompt
                if dialog_result == unreal.AppReturnType.OK:
                    user_prompt = "synthwave cityscape with neon lights"
                    unreal.log(f"Using default prompt: {user_prompt}")
                else:
                    return None
            except Exception as msg_err:
                unreal.log_warning(f"Could not show dialog: {str(msg_err)}")
                return None
        
        # Process the user input if we have it
        if user_prompt:
            # Generate the texture
            try:
                unreal.log(f"Generating texture from prompt: {user_prompt}")
                
                # Use the API to generate a texture
                result = api.generate_texture(user_prompt)
                
                # Check if the result is an error message (starts with "Error:")
                if result and not result.startswith("Error:"):
                    # Show a success message
                    try:
                        unreal.EditorDialog.show_message(
                            title="Texture Generated",
                            message=f"Texture generated successfully: {result}",
                            message_type=unreal.AppMsgType.OK
                        )
                    except:
                        unreal.log(f"Texture generated successfully: {result}")
                    
                    return result
                else:
                    # Show error message with proper title for connection errors
                    try:
                        title = "Generation Failed"
                        
                        # Use a more specific title for connection errors
                        if result and "connect" in result.lower():
                            title = "ComfyUI Connection Error"
                        
                        unreal.EditorDialog.show_message(
                            title=title,
                            message=result if result else "Failed to generate texture. Check log for details.",
                            message_type=unreal.AppMsgType.OK
                        )
                    except:
                        unreal.log_error(result if result else "Failed to generate texture. Check log for details.")
                    
                    return None
            except Exception as gen_err:
                # Show error message
                try:
                    unreal.EditorDialog.show_message(
                        title="Error",
                        message=f"Failed to generate texture: {str(gen_err)}",
                        message_type=unreal.AppMsgType.OK
                    )
                except:
                    unreal.log_error(f"Failed to generate texture: {str(gen_err)}")
                
                return None
        else:
            unreal.log_warning("No prompt provided")
            return None
    except Exception as e:
        unreal.log_error(f"Error in dialog UI: {str(e)}")
        return None

def _console_interface(api):
    """Fall back to a console-based interface."""
    unreal.log("=== Dreamwave Texture Generator ===")
    unreal.log("Enter parameters in Output Log, then run the generate command")
    
    # Register a command for texture generation
    cmd = """
import unreal
import os
import sys

# Get plugin path
plugin_dir = os.path.join(unreal.Paths.project_plugins_dir(), "DreamwaveTexGen", "Content", "Python")
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)

try:
    import dreamwave_texgen_api
    
    # Create API
    api = dreamwave_texgen_api.DreamwaveTexGenAPI()
    
    # Get input parameters - in a real implementation, you'd get these from the user
    prompt = "colorful abstract texture with swirls"
    style = "Vaporwave"
    
    # Generate texture
    result = api.generate_texture(prompt=prompt, style=style)
    
    # Show result
    unreal.log(f"Texture generation result: {result}")
    unreal.EditorDialog.show_message(
        title="Texture Generated",
        message=f"Result: {result}",
        message_type=unreal.AppMsgType.OK
    )
except Exception as e:
    unreal.log_error(f"Failed to generate texture: {str(e)}")
    unreal.EditorDialog.show_message(
        title="Error",
        message=f"Failed to generate texture: {str(e)}",
        message_type=unreal.AppMsgType.OK
    )
"""
    
    try:
        unreal.PythonBPLib.register_command("generate_texture", cmd, "Generate texture with default parameters")
        unreal.log("Registered 'generate_texture' command - run this to generate a texture")
        return True
    except Exception as e:
        unreal.log_error(f"Failed to register command: {str(e)}")
        return False

def build_ui(api, window):
    """Build the UI for the texture generator."""
    # This is a placeholder that would be used for more complex UI implementations
    # In UE 5.5.3, we're using simpler dialog approaches instead
    return None

def create_text_block(text):
    """Helper function to create a text block."""
    text_block = unreal.TextBlock()
    text_block.set_text(text)
    return text_block

def check_comfyui_status():
    """
    Check if the ComfyUI server is running.
    This can be called directly from a menu item.
    """
    try:
        # Import the API module
        import dreamwave_texgen_api
        
        # Get server URL from settings
        from dreamwave_texgen_settings import SETTINGS
        server_url = SETTINGS.ComfyUIServerURL
        if not server_url or server_url == "":
            server_url = "http://127.0.0.1:8188"
        
        # Try to connect to the server
        try:
            import requests
            response = requests.get(f"{server_url}/system_stats", timeout=2)
            if response.status_code == 200:
                # Server is running
                status_msg = f"ComfyUI is running at {server_url}"
                unreal.log(status_msg)
                
                try:
                    # Get some system stats
                    stats = response.json()
                    if stats:
                        ram_stats = stats.get("ram", {})
                        vram_stats = stats.get("vram", {})
                        
                        # Format RAM info
                        if ram_stats:
                            ram_used = ram_stats.get("used", 0) / (1024 * 1024 * 1024)  # Convert to GB
                            ram_total = ram_stats.get("total", 0) / (1024 * 1024 * 1024)  # Convert to GB
                            status_msg += f"\nRAM: {ram_used:.2f}GB / {ram_total:.2f}GB"
                        
                        # Format VRAM info
                        if vram_stats:
                            vram_used = vram_stats.get("used", 0) / (1024 * 1024 * 1024)  # Convert to GB
                            vram_total = vram_stats.get("total", 0) / (1024 * 1024 * 1024)  # Convert to GB
                            status_msg += f"\nVRAM: {vram_used:.2f}GB / {vram_total:.2f}GB"
                except:
                    # Just use basic status message if we can't parse the stats
                    pass
                
                # Show the message
                try:
                    unreal.EditorDialog.show_message(
                        title="ComfyUI Status",
                        message=status_msg,
                        message_type=unreal.AppMsgType.OK
                    )
                except:
                    unreal.log(status_msg)
                
                return True
            else:
                # Server responded but with an error
                status_msg = f"ComfyUI server at {server_url} responded with status code {response.status_code}"
                unreal.log_warning(status_msg)
                
                try:
                    unreal.EditorDialog.show_message(
                        title="ComfyUI Status",
                        message=status_msg,
                        message_type=unreal.AppMsgType.OK
                    )
                except:
                    unreal.log(status_msg)
                
                return False
        except Exception as e:
            # Connection error - server not running
            status_msg = f"ComfyUI is not running at {server_url}\n\nError: {str(e)}"
            unreal.log_warning(status_msg)
            
            try:
                unreal.EditorDialog.show_message(
                    title="ComfyUI Status",
                    message=status_msg,
                    message_type=unreal.AppMsgType.OK
                )
            except:
                unreal.log(status_msg)
            
            return False
    except Exception as e:
        unreal.log_error(f"Failed to check ComfyUI status: {str(e)}")
        
        # Try to show an error dialog
        try:
            unreal.EditorDialog.show_message(
                title="ComfyUI Status Error",
                message=f"Failed to check ComfyUI status: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except:
            print(f"ERROR: Failed to check ComfyUI status: {str(e)}")
        
        return False

def launch_comfyui_server():
    """
    Launch the ComfyUI server if it's not already running.
    This can be called directly from a menu item.
    """
    try:
        # Import the API module
        import dreamwave_texgen_api
        
        # Create the API instance
        api = dreamwave_texgen_api.DreamwaveTexGenAPI()
        
        # Launch the server
        return api.launch_comfyui_server(show_dialog=True)
    except Exception as e:
        unreal.log_error(f"Failed to launch ComfyUI server: {str(e)}")
        
        # Try to show an error dialog
        try:
            unreal.EditorDialog.show_message(
                title="ComfyUI Launch Error",
                message=f"Failed to launch ComfyUI server: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except:
            print(f"ERROR: Failed to launch ComfyUI server: {str(e)}")
        
        return False

# Direct function to open UI
def open_texture_generator_ui():
    """
    Direct entry point function to open the texture generator UI.
    This can be called from the Python console with:
    import dreamwave_texgen_ui; dreamwave_texgen_ui.open_texture_generator_ui()
    """
    try:
        # Import the API module
        import dreamwave_texgen_api
        
        # Create the API instance
        api = dreamwave_texgen_api.DreamwaveTexGenAPI()
        
        # Show the UI
        return show_ui(api)
    except Exception as e:
        unreal.log_error(f"Failed to open texture generator UI: {str(e)}")
        
        # Try to show an error dialog
        try:
            unreal.EditorDialog.show_message(
                title="Dreamwave Error",
                message=f"Failed to open texture generator UI: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except:
            print(f"ERROR: Failed to open texture generator UI: {str(e)}")
        
        return None

# Allow direct execution
if __name__ == "__main__":
    open_texture_generator_ui() 