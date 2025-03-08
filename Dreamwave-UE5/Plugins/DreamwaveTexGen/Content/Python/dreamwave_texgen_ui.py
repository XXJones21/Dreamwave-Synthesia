"""
Dreamwave Texture Generator - UI Module
Provides a UI for the texture generator in Unreal Engine.

This module implements a dialog-based UI for the Dreamwave Texture Generator.
It provides the following functionality:
- A comprehensive dialog for setting texture generation parameters
- Style selection (Vaporwave, Synthwave, Cyberpunk, Retro)
- CLIP Text Encode (Prompt) input
- Resolution selection
- Error handling and user feedback
- ComfyUI server status checking and auto-launching

The UI has two implementations:
1. Dialog-based UI (current): A series of dialogs that guide the user through the texture generation process
2. Window-based UI (future): A comprehensive window with all controls in one place (implementation framework included)

The window-based UI requires the unreal_python_window_lib module, which may not be available in all Unreal Engine versions.
"""

import unreal
import os
import sys
import webbrowser
from functools import partial
import json
import importlib
import time
import threading
import uuid

# Check for requirements
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Check for WebSocket
try:
    import websocket
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

def show_ui(api):
    """Show the UI for the texture generator."""
    try:
        # Try to import Python Window Library
        import unreal_python_window_lib as pwin
        
        # Create a window if the library is available
        window = pwin.create_window(
            title="Dreamwave Texture Generator",
            width=600,
            height=700,
            resize=True
        )
        
        # Build the UI
        built_window = build_ui(api, window)
        if built_window:
            # Show the window
            built_window.show()
            return True
        else:
            # Fall back to simple dialog
            return _show_generator_dialog(api)
            
    except ImportError:
        # Python Window Library not available, use the dialog approach
        unreal.log_warning("Python Window Library not available, using dialog approach")
        return _show_generator_dialog(api)
    except Exception as e:
        # Show error message if possible
        try:
            unreal.EditorDialog.show_message(
                title="Dreamwave Error",
                message=f"Failed to open UI: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except:
            unreal.log_error(f"UI initialization error: {str(e)}")
            
    return None

def _show_generator_dialog(api):
    """Show the most basic dialog interface that works with any UE version."""
    try:
        # Create settings for the dialog
        title = "Dreamwave Texture Generator"
        
        # Use the absolute simplest approach with just OK_CANCEL dialogs
        try:
            # Simplest possible interface - just confirm generation with default settings
            dialog_result = None
            
            # Check if we can use EditorDialog.show_message
            if hasattr(unreal, 'EditorDialog') and hasattr(unreal.EditorDialog, 'show_message'):
                dialog_result = unreal.EditorDialog.show_message(
                    title="Simple Texture Generator",
                    message="Generate a texture with the default prompt and settings?\n\nPrompt: colorful abstract texture with vaporwave style\nStyle: Vaporwave\nResolution: 1024x1024",
                    message_type=unreal.AppMsgType.OK_CANCEL
                )
            # Otherwise, try another approach with EditorDialogLibrary
            elif hasattr(unreal, 'EditorDialogLibrary') and hasattr(unreal.EditorDialogLibrary, 'show_message'):
                dialog_result = unreal.EditorDialogLibrary.show_message(
                    title="Simple Texture Generator",
                    message="Generate a texture with the default prompt and settings?\n\nPrompt: colorful abstract texture with vaporwave style\nStyle: Vaporwave\nResolution: 1024x1024",
                    dialog_type=unreal.AppMsgType.OK_CANCEL
                )
            
            # If user confirmed, generate with default parameters
            if dialog_result == unreal.AppReturnType.OK:
                # Default prompt and settings
                default_prompt = "colorful abstract texture with vaporwave style"
                style = "Vaporwave"
                width = 1024
                height = 1024
                
                # Ask about using FluxSchnell workflow
                use_flux = False
                flux_result = None
                
                if hasattr(unreal, 'EditorDialog') and hasattr(unreal.EditorDialog, 'show_message'):
                    flux_result = unreal.EditorDialog.show_message(
                        title="Generation Model",
                        message="Use FluxSchnell model for faster generation?\n\nRequires FluxSchnell models to be installed.",
                        message_type=unreal.AppMsgType.YES_NO
                    )
                    use_flux = (flux_result == unreal.AppReturnType.YES)
                
                # Enable FluxSchnell if selected
                if hasattr(api, 'settings') and hasattr(api.settings, 'UseFluxWorkflow'):
                    api.settings.UseFluxWorkflow = use_flux
                
                # Log generation attempt
                unreal.log(f"Generating texture with default prompt: {default_prompt}")
                if use_flux:
                    unreal.log("Using FluxSchnell workflow")
                
                # Check if ComfyUI server is running first
                try:
                    import requests
                    server_url = "http://127.0.0.1:8188"
                    response = requests.get(f"{server_url}/system_stats", timeout=2)
                    
                    if response.status_code != 200:
                        # Server error - show message and offer to launch
                        if hasattr(unreal, 'EditorDialog') and hasattr(unreal.EditorDialog, 'show_message'):
                            launch_result = unreal.EditorDialog.show_message(
                                title="ComfyUI Server Error",
                                message="ComfyUI server not responding. Would you like to launch it?",
                                message_type=unreal.AppMsgType.YES_NO
                            )
                            
                            if launch_result == unreal.AppReturnType.YES:
                                # Launch ComfyUI
                                api.launch_comfyui_server()
                                
                                # Show waiting message
                                if hasattr(unreal, 'EditorDialog') and hasattr(unreal.EditorDialog, 'show_message'):
                                    unreal.EditorDialog.show_message(
                                        title="ComfyUI Starting",
                                        message="Waiting for ComfyUI server to start...\nThis may take a minute.",
                                        message_type=unreal.AppMsgType.OK
                                    )
                                
                                # Wait a bit for server to start
                                import time
                                time.sleep(5)
                                
                                # Check if it's running now
                                try:
                                    check_response = requests.get(f"{server_url}/system_stats", timeout=5)
                                    if check_response.status_code != 200:
                                        unreal.log_error("ComfyUI server still not responding after launch attempt")
                                        return None
                                except:
                                    unreal.log_error("ComfyUI server still not responding after launch attempt")
                                    return None
                            else:
                                # User chose not to launch server
                                return None
                        else:
                            # Can't show dialog, just log error
                            unreal.log_error("ComfyUI server not responding")
                            return None
                except Exception as server_err:
                    # Failed to check server, try to launch it
                    unreal.log_warning(f"Could not verify ComfyUI server status: {str(server_err)}")
                    unreal.log("Attempting to launch ComfyUI server...")
                    api.launch_comfyui_server()
                    
                    # Wait a bit for server to start
                    import time
                    time.sleep(5)
                
                # Generate the texture
                try:
                    # Show working message if possible
                    if hasattr(unreal, 'EditorDialog') and hasattr(unreal.EditorDialog, 'show_message'):
                        unreal.EditorDialog.show_message(
                            title="Generating Texture",
                            message="Generating texture...\nThis may take a minute.",
                            message_type=unreal.AppMsgType.OK
                        )
                    
                    # Generate texture
                    result = api.generate_texture(default_prompt, style=style, width=width, height=height)
                    
                    # Check if the result is an error message
                    if result and not result.startswith("Error:"):
                        # Show a success message if possible
                        if hasattr(unreal, 'EditorDialog') and hasattr(unreal.EditorDialog, 'show_message'):
                            unreal.EditorDialog.show_message(
                                title="Success",
                                message=f"Texture generated successfully!\n\nImported to Content/DreamwaveTextures",
                                message_type=unreal.AppMsgType.OK
                            )
                        else:
                            unreal.log(f"Texture generated successfully: {result}")
                            
                        return result
                    else:
                        # Handle error - try to debug ComfyUI connection issue
                        if "400 Client Error" in str(result):
                            unreal.log_error("ComfyUI server returned a 400 error - workflow may be invalid")
                            
                            # Try to restart the server as a fallback
                            if hasattr(unreal, 'EditorDialog') and hasattr(unreal.EditorDialog, 'show_message'):
                                restart_result = unreal.EditorDialog.show_message(
                                    title="ComfyUI Error",
                                    message="ComfyUI workflow error. Would you like to restart the server?",
                                    message_type=unreal.AppMsgType.YES_NO
                                )
                                
                                if restart_result == unreal.AppReturnType.YES:
                                    # Relaunch ComfyUI
                                    api.launch_comfyui_server()
                            
                        # Show error message if possible
                        if hasattr(unreal, 'EditorDialog') and hasattr(unreal.EditorDialog, 'show_message'):
                            unreal.EditorDialog.show_message(
                                title="Error",
                                message=f"Failed to generate texture: {result}",
                                message_type=unreal.AppMsgType.OK
                            )
                        else:
                            unreal.log_error(f"Failed to generate texture: {result}")
                        
                        return None
                except Exception as gen_err:
                    # Failed to generate, show error if possible
                    unreal.log_error(f"Exception during texture generation: {str(gen_err)}")
                    
                    if hasattr(unreal, 'EditorDialog') and hasattr(unreal.EditorDialog, 'show_message'):
                        unreal.EditorDialog.show_message(
                            title="Error",
                            message=f"Failed to generate texture: {str(gen_err)}",
                            message_type=unreal.AppMsgType.OK
                        )
                    
                    return None
                    
        except Exception as dialog_err:
            unreal.log_warning(f"Could not use dialog system: {str(dialog_err)}")
            
            # Ultra-fallback - just generate without any UI
            try:
                unreal.log("Falling back to non-interactive generation")
                default_prompt = "colorful abstract texture with vaporwave style"
                
                # Try to launch ComfyUI if needed
                api.launch_comfyui_server(show_dialog=False)
                
                # Wait a bit for server to start
                import time
                time.sleep(5)
                
                # Generate with defaults
                unreal.log(f"Generating texture with default prompt: {default_prompt}")
                result = api.generate_texture(default_prompt)
                
                if result and not result.startswith("Error:"):
                    unreal.log(f"Texture generation successful: {result}")
                    return result
                else:
                    unreal.log_error(f"Texture generation failed: {result}")
                    return None
            except Exception as fallback_err:
                unreal.log_error(f"Failed to generate texture: {str(fallback_err)}")
                return None
                
    except Exception as e:
        unreal.log_error(f"Error in texture generator dialog: {str(e)}")
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
    # This implements a framework for a more comprehensive UI in the future
    # Currently not being used as we're using the dialog approach instead
    try:
        # If Python Window Library is available, we can build a more comprehensive UI
        import unreal_python_window_lib as pwin
        
        # Create a proper window with text entry boxes and settings
        scroll_box = pwin.SScrollBox()
        
        # Create a vertical box to hold all the UI elements
        vertical_box = pwin.SVerticalBox()
        
        # Add a header
        header_text = pwin.STextBlock(text="Dreamwave Texture Generator")
        header_text.set_font_size(24)
        header_text.set_bold(True)
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(10).with_auto_height().with_h_align(pwin.HAlign.CENTER).with_content(header_text))
        
        # Add a description
        desc_text = pwin.STextBlock(text="Generate AI-powered textures using ComfyUI")
        desc_text.set_font_size(14)
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(5).with_auto_height().with_h_align(pwin.HAlign.CENTER).with_content(desc_text))
        
        # Add a separator
        separator = pwin.SSeparator()
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(10).with_auto_height().with_content(separator))
        
        # Style selection section
        style_section_text = pwin.STextBlock(text="Texture Style")
        style_section_text.set_font_size(16)
        style_section_text.set_bold(True)
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(5).with_auto_height().with_content(style_section_text))
        
        # Style combo box
        style_combo = pwin.SComboBox()
        styles = ["Vaporwave", "Synthwave", "Cyberpunk", "Retro"]
        for style in styles:
            style_combo.add_option(style)
        style_combo.set_selected_option("Vaporwave")  # Default
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(5).with_auto_height().with_content(style_combo))
        
        # Workflow selection section
        workflow_section_text = pwin.STextBlock(text="Generation Model")
        workflow_section_text.set_font_size(16)
        workflow_section_text.set_bold(True)
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(10, 5, 5, 5).with_auto_height().with_content(workflow_section_text))
        
        # Workflow options in a horizontal box with radio buttons
        workflow_box = pwin.SHorizontalBox()
        workflow_group = pwin.SRadioButtonGroup()
        
        # Standard workflow option
        standard_radio = pwin.SRadioButton(text="Standard", group=workflow_group)
        standard_radio.set_tool_tip("Use the standard workflow with Stable Diffusion models")
        workflow_box.add_slot(pwin.SHorizontalBox.FSlot().with_auto_width().with_padding(5, 0, 20, 0).with_content(standard_radio))
        
        # FluxSchnell workflow option
        flux_radio = pwin.SRadioButton(text="FluxSchnell (Fast)", group=workflow_group)
        flux_radio.set_tool_tip("Use the FluxSchnell workflow for faster generation (requires FluxSchnell models)")
        workflow_box.add_slot(pwin.SHorizontalBox.FSlot().with_auto_width().with_content(flux_radio))
        
        # Set the default selection
        standard_radio.set_is_checked(True)
        
        # Add the workflow box to the main vertical box
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(5).with_auto_height().with_content(workflow_box))
        
        # CLIP Text Encode section (Prompt)
        prompt_section_text = pwin.STextBlock(text="CLIP Text Encode (Prompt)")
        prompt_section_text.set_font_size(16)
        prompt_section_text.set_bold(True)
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(10, 5, 5, 5).with_auto_height().with_content(prompt_section_text))
        
        # Prompt multi-line text entry box
        prompt_text = pwin.SMultiLineTextBox()
        prompt_text.set_hint_text("Enter a detailed description of the texture you want to generate...")
        prompt_text.set_text("")  # Empty by default
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(5).with_height(100).with_content(prompt_text))
        
        # Negative Prompt section
        negative_section_text = pwin.STextBlock(text="Negative Prompt (what to avoid)")
        negative_section_text.set_font_size(16)
        negative_section_text.set_bold(True)
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(10, 5, 5, 5).with_auto_height().with_content(negative_section_text))
        
        # Negative Prompt multi-line text entry box
        negative_text = pwin.SMultiLineTextBox()
        negative_text.set_hint_text("Enter features you want to avoid (optional)...")
        negative_text.set_text("blurry, low quality, distorted, ugly")  # Default
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(5).with_height(80).with_content(negative_text))
        
        # Resolution section
        resolution_section_text = pwin.STextBlock(text="Texture Resolution")
        resolution_section_text.set_font_size(16)
        resolution_section_text.set_bold(True)
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(10, 5, 5, 5).with_auto_height().with_content(resolution_section_text))
        
        # Resolution options in a horizontal box
        resolution_box = pwin.SHorizontalBox()
        
        # Width input
        width_box = pwin.SHorizontalBox()
        width_label = pwin.STextBlock(text="Width:")
        width_box.add_slot(pwin.SHorizontalBox.FSlot().with_auto_width().with_v_align(pwin.VAlign.CENTER).with_content(width_label))
        width_input = pwin.SSpinBox()
        width_input.set_min_value(256)
        width_input.set_max_value(4096)
        width_input.set_value(1024)  # Default
        width_box.add_slot(pwin.SHorizontalBox.FSlot().with_padding(5, 0, 20, 0).with_auto_width().with_content(width_input))
        
        # Height input
        height_box = pwin.SHorizontalBox()
        height_label = pwin.STextBlock(text="Height:")
        height_box.add_slot(pwin.SHorizontalBox.FSlot().with_auto_width().with_v_align(pwin.VAlign.CENTER).with_content(height_label))
        height_input = pwin.SSpinBox()
        height_input.set_min_value(256)
        height_input.set_max_value(4096)
        height_input.set_value(1024)  # Default
        height_box.add_slot(pwin.SHorizontalBox.FSlot().with_padding(5, 0, 0, 0).with_auto_width().with_content(height_input))
        
        # Add width and height boxes to the resolution box
        resolution_box.add_slot(pwin.SHorizontalBox.FSlot().with_auto_width().with_content(width_box))
        resolution_box.add_slot(pwin.SHorizontalBox.FSlot().with_auto_width().with_content(height_box))
        
        # Add resolution box to the main vertical box
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(5).with_auto_height().with_content(resolution_box))
        
        # Checkbox for "Import to Content Browser"
        import_box = pwin.SHorizontalBox()
        import_checkbox = pwin.SCheckBox()
        import_checkbox.set_is_checked(True)  # Default is checked
        import_box.add_slot(pwin.SHorizontalBox.FSlot().with_auto_width().with_content(import_checkbox))
        import_label = pwin.STextBlock(text="Import texture to Content Browser")
        import_box.add_slot(pwin.SHorizontalBox.FSlot().with_padding(5, 0, 0, 0).with_auto_width().with_content(import_label))
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(5).with_auto_height().with_content(import_box))
        
        # Add some spacing
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(10).with_auto_height())
        
        # Generate button
        generate_button = pwin.SButton(text="Generate Texture")
        generate_button.set_tool_tip("Generate a texture with the specified settings")
        vertical_box.add_slot(pwin.SVerticalBox.FSlot().with_padding(5).with_auto_height().with_h_align(pwin.HAlign.CENTER).with_content(generate_button))
        
        # Add the vertical box to the scroll box
        scroll_box.add_child(vertical_box)
        
        # Set up the generate button callback
        def on_generate_clicked():
            try:
                # Get the values from the UI
                selected_style = style_combo.get_selected_option()
                user_prompt = prompt_text.get_text()
                neg_prompt = negative_text.get_text()
                width = width_input.get_value()
                height = height_input.get_value()
                should_import = import_checkbox.is_checked()
                use_flux = flux_radio.is_checked()
                
                # Validate the prompt
                if not user_prompt or user_prompt.strip() == "":
                    pwin.show_message_dialog("Error", "Please enter a prompt for the texture.", pwin.AppMsgType.OK)
                    return
                
                # Set setting for FluxSchnell workflow if checked
                if hasattr(api, 'settings') and hasattr(api.settings, 'UseFluxWorkflow'):
                    api.settings.UseFluxWorkflow = use_flux
                
                # If we have FluxSchnell selected, validate the requirements
                if use_flux:
                    unreal.log("Validating FluxSchnell requirements...")
                    if hasattr(api.bridge, 'validate_flux_requirements'):
                        if not api.bridge.validate_flux_requirements():
                            pwin.show_message_dialog(
                                "FluxSchnell Models Not Found", 
                                "Required models for FluxSchnell workflow were not found.\n\n" +
                                "Please download the required models from:\n" +
                                "https://comfyanonymous.github.io/ComfyUI_examples/flux/\n\n" +
                                "Required files:\n" +
                                "- models/unet/flux1-schnell.safetensors\n" +
                                "- models/clip/t5xxl_fp16.safetensors\n" +
                                "- models/clip/clip_l.safetensors\n" +
                                "- models/vae/ae.safetensors", 
                                pwin.AppMsgType.OK
                            )
                            return
                
                # Create a progress dialog
                progress_dialog = pwin.SProgressDialog()
                progress_dialog.set_title("Generating Texture")
                progress_dialog.set_message(f"Initializing {selected_style} texture generation...")
                progress_dialog.set_progress(0)
                progress_dialog.set_should_close_on_complete(False)
                progress_dialog.show()
                
                # Create a unique ID for tracking this generation
                generation_id = str(uuid.uuid4())
                
                # Create a thread to monitor generation progress
                progress_thread = None
                
                if WEBSOCKET_AVAILABLE and hasattr(api.bridge, 'ws') and api.bridge.ws:
                    # Setup a thread to monitor websocket messages for progress
                    def update_progress():
                        prompt_id = None
                        start_time = time.time()
                        timeout = 180  # 3 minutes timeout
                        
                        while time.time() - start_time < timeout:
                            # Check if we have a prompt ID yet
                            if not prompt_id and hasattr(api.bridge, 'execution_status'):
                                # Look for a new prompt ID in the execution status
                                for pid, status in api.bridge.execution_status.items():
                                    if status.get("generation_id") == generation_id:
                                        prompt_id = pid
                                        break
                            
                            # If we have a prompt ID, monitor its status
                            if prompt_id and hasattr(api.bridge, 'get_prompt_status'):
                                status = api.bridge.get_prompt_status(prompt_id)
                                
                                if status["status"] == "running":
                                    # Update progress dialog
                                    current_node = status.get("current_node", "Unknown")
                                    progress = status.get("progress", 0)
                                    
                                    # Update the progress dialog
                                    if progress > 0:
                                        progress_dialog.set_progress(progress)
                                    
                                    # Update the message with the current node
                                    node_msg = f"Processing node: {current_node}" if current_node else "Initializing..."
                                    progress_dialog.set_message(f"Generating {selected_style} texture ({width}x{height})...\n{node_msg}")
                                    
                                elif status["status"] == "completed":
                                    # Generation completed
                                    progress_dialog.set_progress(100)
                                    progress_dialog.set_message("Generation complete! Processing results...")
                                    time.sleep(0.5)  # Brief pause to show 100%
                                    return
                                    
                                elif status["status"] == "error":
                                    # Error occurred
                                    error_details = status["errors"][-1] if status["errors"] else {"error_message": "Unknown error"}
                                    progress_dialog.set_message(f"Error: {error_details.get('error_message', 'Unknown error')}")
                                    time.sleep(2)  # Show error for a moment
                                    progress_dialog.close()
                                    return
                            
                            # Short sleep to avoid hammering the CPU
                            time.sleep(0.5)
                        
                        # If we reach here, we timed out
                        progress_dialog.set_message("Generation timed out. Check logs for details.")
                        time.sleep(2)
                        progress_dialog.close()
                    
                    # Start the progress monitoring thread
                    progress_thread = threading.Thread(target=update_progress)
                    progress_thread.daemon = True
                    progress_thread.start()
                
                # Store the generation ID in the bridge's execution status object
                if hasattr(api.bridge, 'generation_id'):
                    api.bridge.generation_id = generation_id
                
                # Generate the texture
                result = None
                
                if use_flux and hasattr(api.bridge, 'generate_with_flux_workflow'):
                    # Use FluxSchnell workflow directly
                    result = api.bridge.generate_with_flux_workflow(
                        prompt=user_prompt,
                        negative_prompt=neg_prompt,
                        width=width,
                        height=height
                    )
                    
                    # Import if successful and requested
                    if result and os.path.exists(result) and should_import:
                        texture_name = f"T_Flux_{os.path.basename(result).split('.')[0]}"
                        api.import_texture(result, texture_name)
                else:
                    # Use standard API
                    style_prompt = api.get_style_preset(selected_style) if hasattr(api, 'get_style_preset') else None
                    full_prompt = f"{user_prompt}, {style_prompt}" if style_prompt else user_prompt
                    
                    # Use normal generate_texture method
                    result = api.generate_texture(full_prompt, style=selected_style, width=width, height=height)
                
                # Close the progress dialog
                progress_dialog.close()
                
                # Show results
                if result and isinstance(result, str) and os.path.exists(result):
                    # Success - show successful result
                    pwin.show_message_dialog(
                        "Success", 
                        f"Texture generated successfully!\n\nImported to: Content/DreamwaveTextures", 
                        pwin.AppMsgType.OK
                    )
                elif result and not result.startswith("Error:"):
                    # Some other success case
                    pwin.show_message_dialog(
                        "Success", 
                        f"Texture operation completed: {result}", 
                        pwin.AppMsgType.OK
                    )
                else:
                    # Error case
                    pwin.show_message_dialog(
                        "Error", 
                        f"Failed to generate texture: {result}", 
                        pwin.AppMsgType.OK
                    )
            except Exception as e:
                # Show error dialog
                pwin.show_message_dialog("Error", f"An error occurred: {str(e)}", pwin.AppMsgType.OK)
                # Also log the full exception
                unreal.log_error(f"Exception in texture generation: {str(e)}")
                import traceback
                unreal.log_error(traceback.format_exc())
        
        # Set the button click callback
        generate_button.set_on_clicked(on_generate_clicked)
        
        # Add the UI to the window
        window.set_content(scroll_box)
        
        return window
    except ImportError:
        # Python Window Library not available, use the dialog approach instead
        unreal.log_warning("Python Window Library not available, using dialog approach instead")
        return None
    except Exception as e:
        unreal.log_error(f"Error building UI: {str(e)}")
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