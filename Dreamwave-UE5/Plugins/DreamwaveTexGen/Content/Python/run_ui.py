"""
Simple script to directly open the Dreamwave Texture Generator UI.
You can run this script directly from the Unreal Engine Python console:
py "D:/Tools/Dreamwave-Synthesia/Dreamwave-UE5/Plugins/DreamwaveTexGen/Content/Python/run_ui.py"
"""

import unreal
import os
import sys
import traceback

def main():
    """Open the Dreamwave Texture Generator UI."""
    unreal.log("Starting Dreamwave Texture Generator...")
    
    try:
        # Make sure current directory is in path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        if script_dir not in sys.path:
            sys.path.append(script_dir)
            unreal.log(f"Added {script_dir} to sys.path")
        
        # Import the API module
        unreal.log("Importing API module...")
        import dreamwave_texgen_api
        
        # Simple dialog-based texture generation
        unreal.log("Starting dialog-based UI...")
        _run_dialog_interface(dreamwave_texgen_api.DreamwaveTexGenAPI())
        
        unreal.log("Dreamwave Texture Generator completed")
        return True
    except Exception as e:
        error_msg = f"Failed to open UI: {str(e)}\n{traceback.format_exc()}"
        unreal.log_error(error_msg)
        
        # Show error dialog with correct parameters for UE 5.5.3
        unreal.EditorDialog.show_message(
            title="Dreamwave Texture Generator Error",
            message=f"Error: {str(e)}",
            message_type=unreal.AppMsgType.OK
        )
        return False

def _run_dialog_interface(api):
    """Simple dialog-based texture generation interface."""
    # Show welcome message
    welcome = unreal.EditorDialog.show_message(
        title="Dreamwave Texture Generator",
        message="Welcome to Dreamwave Texture Generator.\nGenerate AI textures for your project?",
        message_type=unreal.AppMsgType.OK_CANCEL
    )
    
    if welcome == unreal.AppReturnType.OK:
        # Get style selection first
        styles = ["Vaporwave", "Synthwave", "Cyberpunk", "Retro"]
        style_choice = unreal.EditorDialog.show_message(
            title="Select Style",
            message="Choose a texture style:\n1. Vaporwave\n2. Synthwave\n3. Cyberpunk\n4. Retro",
            message_type=unreal.AppMsgType.ONE_TWO_THREE_FOUR
        )
        
        # Map the response to a style
        style_index = 0  # Default to Vaporwave
        if style_choice == unreal.AppReturnType.ONE:
            style_index = 0
        elif style_choice == unreal.AppReturnType.TWO:
            style_index = 1
        elif style_choice == unreal.AppReturnType.THREE:
            style_index = 2
        elif style_choice == unreal.AppReturnType.FOUR:
            style_index = 3
            
        style = styles[style_index]
        unreal.log(f"Selected style: {style}")
        
        # Get prompt from user
        prompt = unreal.EditorDialog.prompt_for_input(
            title="Texture Prompt",
            prompt=f"Enter a description for your {style} texture:"
        )
        
        if prompt and prompt.strip():
            # Show generating message
            unreal.log(f"Generating texture with prompt: {prompt}, style: {style}")
            
            # Progress dialog
            unreal.EditorDialog.show_message(
                title="Generating Texture",
                message=f"Generating {style} texture with prompt:\n{prompt}\n\nThis may take a moment...",
                message_type=unreal.AppMsgType.OK
            )
            
            # Generate the texture
            result = api.generate_texture(prompt=prompt, style=style)
            
            # Show success message
            unreal.EditorDialog.show_message(
                title="Texture Generated",
                message=f"Successfully generated texture: {result}",
                message_type=unreal.AppMsgType.OK
            )
            
            return True
    
    return False

# Run when executed directly
if __name__ == "__main__":
    main() 