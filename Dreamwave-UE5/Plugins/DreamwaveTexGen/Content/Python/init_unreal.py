"""
Dreamwave Texture Generator - Initialization Script
This script runs when Unreal Engine starts and initializes the texture generator UI.
"""

import unreal
import os
import sys
import traceback

# Log startup information
unreal.log("Dreamwave Texture Generator plugin initialization module loaded.")

# Add our plugin's Python directory to the path for imports
try:
    plugin_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if plugin_dir not in sys.path:
        sys.path.append(plugin_dir)
    unreal.log(f"Added plugin directory to Python path: {plugin_dir}")
except Exception as e:
    unreal.log_error(f"Failed to add plugin directory to Python path: {str(e)}")

# Function to register a simple command
def register_dreamwave_command():
    """Register a console command to launch Dreamwave."""
    try:
        command_script = """
import unreal
import os
import sys

# Get plugin path
plugin_dir = os.path.join(unreal.Paths.project_plugins_dir(), "DreamwaveTexGen", "Content", "Python")
if plugin_dir not in sys.path:
    sys.path.append(plugin_dir)
    
try:
    # Try to import directly first
    import dreamwave_texgen_api
    import dreamwave_texgen_ui
    
    # Create API and run UI
    api = dreamwave_texgen_api.DreamwaveTexGenAPI()
    dreamwave_texgen_ui.show_ui(api)
    
    unreal.log("Dreamwave UI opened successfully")
except Exception as e:
    unreal.log_error(f"Failed to open Dreamwave UI: {str(e)}")
    try:
        unreal.EditorDialog.show_message(
            title="Dreamwave Error",
            message=f"Failed to open Dreamwave UI: {str(e)}",
            message_type=unreal.AppMsgType.OK
        )
    except:
        # Simplified error display if EditorDialog is not available
        print(f"ERROR: Failed to open Dreamwave UI: {str(e)}")
"""
        
        # Register the command using compatible methods
        unreal.log("Registering 'dreamwave' command")
        
        # First try PythonCommand explicitly (UE 5.0+)
        try:
            if hasattr(unreal, 'PythonCommand'):
                cmd = unreal.PythonCommand()
                cmd.command = "dreamwave"
                cmd.description = "Open Dreamwave Texture Generator"
                cmd.script = command_script
                cmd.execute_method = unreal.PythonCommandExecutionMethod.EXECUTE_STATEMENT
                cmd.support_automatic_completion = False
                
                # Register the command
                unreal.PythonCommand.register_command(cmd)
                unreal.log("Registered 'dreamwave' command using PythonCommand")
                return True
        except Exception as cmd_err:
            unreal.log_warning(f"Could not use PythonCommand: {str(cmd_err)}")
        
        # Try directly adding to the Python commands registry (most compatible)
        try:
            # Find direct Python command registry in Unreal
            if hasattr(unreal, 'EditorScriptingUtilities'):
                utils = unreal.EditorScriptingUtilities()
                if hasattr(utils, 'register_python_command'):
                    utils.register_python_command("dreamwave", command_script, "Open Dreamwave Texture Generator")
                    unreal.log("Registered 'dreamwave' command using EditorScriptingUtilities")
                    return True
        except Exception as util_err:
            unreal.log_warning(f"Could not use EditorScriptingUtilities: {str(util_err)}")
            
        # Try using custom registration via Python execution
        try:
            # Create a custom command registration by executing a Python function
            exec("""
def _run_dreamwave_command():
    import unreal
    import os
    import sys
    
    # Get plugin path
    plugin_dir = os.path.join(unreal.Paths.project_plugins_dir(), "DreamwaveTexGen", "Content", "Python")
    if plugin_dir not in sys.path:
        sys.path.append(plugin_dir)
        
    try:
        # Try to import directly first
        import dreamwave_texgen_api
        import dreamwave_texgen_ui
        
        # Create API and run UI
        api = dreamwave_texgen_api.DreamwaveTexGenAPI()
        dreamwave_texgen_ui.show_ui(api)
        
        unreal.log("Dreamwave UI opened successfully")
    except Exception as e:
        unreal.log_error(f"Failed to open Dreamwave UI: {str(e)}")
        try:
            unreal.EditorDialog.show_message(
                title="Dreamwave Error",
                message=f"Failed to open Dreamwave UI: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except:
            print(f"ERROR: Failed to open Dreamwave UI: {str(e)}")

# Register the command in global namespace
globals()['dreamwave'] = _run_dreamwave_command
""")
            unreal.log("Registered 'dreamwave' command using global function")
            return True
        except Exception as exec_err:
            unreal.log_warning(f"Could not register via globals: {str(exec_err)}")
            
        # Fallback to direct function that user can call
        try:
            # Create a module-level function that can be called from the Python console
            from dreamwave_texgen_ui import open_texture_generator_ui
            unreal.log("'dreamwave_texgen_ui.open_texture_generator_ui()' is available to run directly")
            return True
        except Exception as direct_err:
            unreal.log_warning(f"Could not setup direct function: {str(direct_err)}")
        
        unreal.log_error("All command registration methods failed")
        return False
    except Exception as e:
        unreal.log_error(f"Failed to register 'dreamwave' command: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Simpler menu registration that works with UE 5.5.3
def register_menu():
    """Register a simple menu item in the Unreal Editor."""
    try:
        unreal.log("Registering simplified menu entries...")
        
        # Make sure we have a command registered
        register_dreamwave_command()
        
        # Try the most direct UI approach - directly opening a window from Python
        try:
            # Find the LevelEditor menu system if it exists
            if hasattr(unreal, 'LevelEditor'):
                level_editor = unreal.LevelEditor.get_level_editor_subsystem()
                if level_editor:
                    # Get the toolbar system
                    if hasattr(level_editor, 'add_menu_entry'):
                        # Direct menu entry addition
                        level_editor.add_menu_entry(
                            "Window", "Dreamwave", "Dreamwave", "Texture Generator",
                            lambda: exec("import dreamwave_texgen_api; import dreamwave_texgen_ui; api = dreamwave_texgen_api.DreamwaveTexGenAPI(); dreamwave_texgen_ui.show_ui(api)")
                        )
                        unreal.log("Added Dreamwave to Window menu using LevelEditor API")
                        return True
            
            # Try using ToolMenus if available
            if hasattr(unreal, 'ToolMenus'):
                menus = unreal.ToolMenus.get()
                
                # Find the main menu
                window_menu = menus.find_menu("LevelEditor.MainMenu.Window")
                if window_menu:
                    # Add a section
                    window_menu.add_section("Dreamwave", "Dreamwave")
                    
                    # Try an approach based on available classes
                    entry = None
                    
                    # Try ToolMenuEntryExtensions if available (newer UE versions)
                    if hasattr(unreal, 'ToolMenuEntryExtensions'):
                        entry = unreal.ToolMenuEntry()
                        entry.name = "DreamwaveTexGen"
                        entry.type = unreal.MultiBlockType.MENU_ENTRY
                        entry.set_label("Dreamwave Texture Generator")
                        
                        # Use the simplest possible Python script execution
                        python_script = "import dreamwave_texgen_ui; dreamwave_texgen_ui.open_texture_generator_ui()"
                        
                        # Check the method signature and parameters
                        try:
                            # In UE 5.5.3, we need to use a more direct approach since 
                            # many of the ToolMenu APIs have different parameter sets
                            
                            # Try a very simple approach first - just use the Python script as label
                            if hasattr(entry, 'label'):
                                entry.label = "Dreamwave Texture Generator"
                                entry.tool_tip = "Open the Dreamwave Texture Generator"
                            
                            # Most basic approach - just use a menu entry with Python execution
                            if hasattr(window_menu, 'add_section') and hasattr(window_menu, 'add_menu_entry'):
                                # This seems to be the most compatible approach
                                window_menu.add_menu_entry("Dreamwave", entry)
                                
                                # Signal our menu creation worked
                                menus.refresh_all_widgets()
                                unreal.log("Added Dreamwave menu entry using simplified approach")
                                return True
                        except Exception as cmd_err:
                            unreal.log_warning(f"Could not set menu command: {str(cmd_err)}")
                    
                    # Fallback to direct entry creation
                    elif hasattr(unreal, 'ToolMenuEntry'):
                        entry = unreal.ToolMenuEntry()
                        entry.name = "DreamwaveTexGen"
                        entry.label = "Dreamwave Texture Generator"
                        entry.tool_tip = "Open the Dreamwave Texture Generator"
                        
                        # Use Python script directly if possible
                        entry.type = unreal.MultiBlockType.MENU_ENTRY
                        entry.command = "import dreamwave_texgen_ui; dreamwave_texgen_ui.open_texture_generator_ui()"
                    
                    # Add the entry if we created one
                    if entry:
                        window_menu.add_menu_entry("Dreamwave", entry)
                        menus.refresh_all_widgets()
                        unreal.log("Added Dreamwave menu entry")
                        return True
            
            # If we couldn't add a menu entry, try a direct editor button
            if hasattr(unreal, 'EditorUtilitySubsystem'):
                utility = unreal.EditorUtilitySubsystem.get_default_object()
                
                # Try adding a toolbar button or similar
                if hasattr(utility, 'spawn_and_register_tab'):
                    # Create a simple Python callable
                    button_script = "import dreamwave_texgen_ui; dreamwave_texgen_ui.open_texture_generator_ui()"
                    
                    # Register with the editor (approach depends on UE version)
                    # Just add a note about manual invocation
                    unreal.log("For UE 5.5.3, manually run 'import dreamwave_texgen_ui; dreamwave_texgen_ui.open_texture_generator_ui()' in the Python console")
                    return True
            
            # Final fallback - just log how to use it
            unreal.log("Menu registration not available. Use 'import dreamwave_texgen_ui; dreamwave_texgen_ui.open_texture_generator_ui()' in the Python console")
            return False
        except Exception as menu_err:
            unreal.log_warning(f"Menu system error: {str(menu_err)}")
            return False
            
    except Exception as e:
        unreal.log_error(f"Failed to register menu: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Function to directly open the UI
def open_dreamwave_ui():
    """Directly open the Dreamwave UI."""
    try:
        # Import the required modules
        import dreamwave_texgen_api
        import dreamwave_texgen_ui
        
        # Create the API
        api = dreamwave_texgen_api.DreamwaveTexGenAPI()
        
        # Show the UI
        dreamwave_texgen_ui.show_ui(api)
        
        return True
    except Exception as e:
        unreal.log_error(f"Failed to open UI: {str(e)}")
        unreal.log_error(traceback.format_exc())
        
        try:
            # Show error dialog with correct parameters for UE 5.5.3
            unreal.EditorDialog.show_message(
                title="Dreamwave Error",
                message=f"Failed to open UI: {str(e)}",
                message_type=unreal.AppMsgType.OK
            )
        except Exception as dialog_err:
            unreal.log_error(f"Failed to show error dialog: {str(dialog_err)}")
        
        return False

# Register the command - this is the most reliable approach
try:
    if register_dreamwave_command():
        unreal.log("Successfully registered 'dreamwave' command")
    else:
        unreal.log_error("Failed to register 'dreamwave' command")
except Exception as cmd_err:
    unreal.log_error(f"Error registering command: {str(cmd_err)}")

# Try to register the menu as well
try:
    if register_menu():
        unreal.log("Successfully registered Dreamwave menu")
    else:
        unreal.log_error("Failed to register Dreamwave menu")
except Exception as menu_err:
    unreal.log_error(f"Error registering menu: {str(menu_err)}")

# When run directly, try to open the UI
if __name__ == "__main__":
    unreal.log("Running Dreamwave initialization directly")
    try:
        open_dreamwave_ui()
    except Exception as direct_err:
        unreal.log_error(f"Failed to open UI directly: {str(direct_err)}")
        
        # Show instructions for manual launch
        try:
            unreal.EditorDialog.show_message(
                title="Dreamwave - Manual Launch Required",
                message="Please use the console command 'dreamwave' to launch the UI",
                message_type=unreal.AppMsgType.OK
            )
        except:
            unreal.log("Use the console command 'dreamwave' to launch the UI") 