"""
Quick Dreamwave launcher script
Run this from the Unreal Engine Python console with:
py "D:/Tools/Dreamwave-Synthesia/Dreamwave-UE5/Content/Python/dreamwave.py"
"""

import unreal
import os
import sys
import traceback

def launch_dreamwave():
    """Launch the Dreamwave Texture Generator UI."""
    try:
        unreal.log("Launching Dreamwave Texture Generator...")
        
        # Get the plugin path
        plugin_dir = os.path.join(unreal.Paths.project_plugins_dir(), "DreamwaveTexGen", "Content", "Python")
        
        # Add to path if needed
        if plugin_dir not in sys.path:
            sys.path.append(plugin_dir)
            unreal.log(f"Added plugin path to sys.path: {plugin_dir}")
        
        # Import API and process
        try:
            unreal.log("Importing API...")
            import dreamwave_texgen_api
            api = dreamwave_texgen_api.DreamwaveTexGenAPI()
            
            # Run UI or fallback to direct generation
            try:
                unreal.log("Showing UI...")
                import dreamwave_texgen_ui
                dreamwave_texgen_ui.show_ui(api)
                unreal.log("UI opened successfully!")
            except Exception as ui_err:
                unreal.log_error(f"UI failed to open: {str(ui_err)}")
                unreal.log("Falling back to direct texture generation...")
                
                # Fallback to direct texture generation without UI
                # Show a dialog to get the prompt
                result = unreal.EditorDialog.show_message(
                    title="Dreamwave Texture Generator", 
                    message="UI failed to open. Generate a texture with default settings?",
                    message_type=unreal.AppMsgType.OK_CANCEL
                )
                
                if result == unreal.AppReturnType.OK:
                    # Get a prompt from the user
                    prompt = unreal.EditorDialog.prompt_for_input(
                        title="Texture Prompt",
                        prompt="Enter a description for your texture:"
                    )
                    
                    if prompt and prompt.strip():
                        # Generate the texture with default settings
                        unreal.log(f"Generating texture with prompt: {prompt}")
                        result = api.generate_texture(prompt=prompt, style="Vaporwave")
                        
                        # Show the result
                        unreal.EditorDialog.show_message(
                            title="Texture Generated",
                            message=f"Result: {result}",
                            message_type=unreal.AppMsgType.OK
                        )
                        return True
                
            return True
        except ImportError as ie:
            unreal.log_error(f"Failed to import required modules: {str(ie)}")
            unreal.log_error(traceback.format_exc())
            
            # Display error to user
            unreal.EditorDialog.show_message(
                title="Module Import Error",
                message=f"Failed to import required modules:\n{str(ie)}\n\nMake sure the plugin is properly installed.",
                message_type=unreal.AppMsgType.OK
            )
            return False
    except Exception as e:
        unreal.log_error(f"Failed to launch Dreamwave: {str(e)}")
        unreal.log_error(traceback.format_exc())
        
        # Show error message
        try:
            unreal.EditorDialog.show_message(
                title="Dreamwave Error",
                message=f"Failed to launch Dreamwave: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except Exception as dialog_err:
            unreal.log_error(f"Dialog error: {str(dialog_err)}")
            
        return False

# Register a console command for easy access
try:
    cmd = """
import sys
import os
import unreal

# Execute the dreamwave.py script
script_path = os.path.join(unreal.Paths.project_content_dir(), "Python", "dreamwave.py")
if os.path.exists(script_path):
    with open(script_path, 'r') as f:
        exec(f.read())
    
    # Launch Dreamwave
    if 'launch_dreamwave' in globals():
        launch_dreamwave()
else:
    unreal.log_error(f"Dreamwave script not found at: {script_path}")
"""
    
    # Register the command
    unreal.PythonBPLib.register_command("dreamwave", cmd, "Launch Dreamwave Texture Generator")
    unreal.log("Registered 'dreamwave' console command")
except Exception as e:
    unreal.log_error(f"Failed to register console command: {str(e)}")

# Auto-run when executed directly
if __name__ == "__main__":
    launch_dreamwave() 