"""
Dreamwave Texture Generator - Initialization Script
This script runs when Unreal Engine starts and registers a Dreamwave toolbar button
and main menu entries for accessing the texture generation tools.

The toolbar implementation uses the UE 5.5 extension system to add UI elements
rather than directly accessing toolbar paths, which provides better compatibility
across different Unreal Engine versions.
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
    """Register a console command to launch Dreamwave.
    
    This creates a global Python command 'dreamwave' that can be run from
    the Unreal Engine console or Python command line.
    """
    try:
        # Create a global function
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
    except Exception as e:
        unreal.log_error(f"Failed to register 'dreamwave' command: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

def register_dreamwave_toolbar():
    """Register Dreamwave menu and toolbar button using the UE 5.5 extension system.
    
    This method:
    1. Creates a Dreamwave menu in the main menu bar
    2. Adds three sub-menu items for Texture Generator, Launch ComfyUI, and Check Status
    3. Adds a toolbar button that links to the Texture Generator
    
    Uses the recommended extension-based approach rather than direct menu path access.
    """
    try:
        unreal.log("Registering Dreamwave toolbar button...")
        
        # Get ToolMenus
        menus = unreal.ToolMenus.get()
        if not menus:
            unreal.log_error("Failed to get ToolMenus instance")
            return False
        
        # Get the Level Editor context menu
        level_menu_ext = menus.extend_menu("LevelEditor.MainMenu")
        if not level_menu_ext:
            unreal.log_error("Failed to extend LevelEditor.MainMenu")
            return False
        
        # Create a new Dreamwave menu
        dreamwave_menu = level_menu_ext.add_sub_menu(
            owner="DreamwavePlugin",
            section_name="Content",
            name="DreamwaveMenu",
            label="Dreamwave"
        )
        
        if not dreamwave_menu:
            unreal.log_error("Failed to create Dreamwave menu")
            return False
        
        # Add a section to the menu
        dreamwave_menu.add_section("DreamwaveCommands", "Dreamwave")
        
        # Add menu items to the dropdown
        # 1. Texture Generator entry
        texgen_entry = unreal.ToolMenuEntry(type=unreal.MultiBlockType.MENU_ENTRY, name="DreamwaveTexGen")
        texgen_entry.set_label("Texture Generator")
        texgen_entry.set_tool_tip("Open Dreamwave Texture Generator")
        texgen_entry.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON, 
            string="import dreamwave_command; dreamwave_command.run_dreamwave()",
            custom_type=""
        )
        dreamwave_menu.add_menu_entry("DreamwaveCommands", texgen_entry)
        
        # 2. Launch ComfyUI entry
        launch_entry = unreal.ToolMenuEntry(type=unreal.MultiBlockType.MENU_ENTRY, name="DreamwaveLaunchComfyUI")
        launch_entry.set_label("Launch ComfyUI Server")
        launch_entry.set_tool_tip("Start the ComfyUI backend server")
        launch_entry.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON,
            string="import dreamwave_command; dreamwave_command.launch_comfyui()",
            custom_type=""
        )
        dreamwave_menu.add_menu_entry("DreamwaveCommands", launch_entry)
        
        # 3. Check Status entry
        status_entry = unreal.ToolMenuEntry(type=unreal.MultiBlockType.MENU_ENTRY, name="DreamwaveCheckStatus")
        status_entry.set_label("Check ComfyUI Status")
        status_entry.set_tool_tip("Check if ComfyUI server is running")
        status_entry.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON,
            string="import dreamwave_command; dreamwave_command.check_comfyui()",
            custom_type=""
        )
        dreamwave_menu.add_menu_entry("DreamwaveCommands", status_entry)
        
        # Now add a button to the toolbar
        # Get a reference to the level editor toolbar using the extension system
        toolbar_extension = menus.extend_menu("LevelEditor.LevelEditorToolBar")
        if not toolbar_extension:
            unreal.log_error("Failed to extend LevelEditor.LevelEditorToolBar")
            return False
        
        # Add a section for Dreamwave
        toolbar_extension.add_section("Dreamwave", "Dreamwave", insert_type=unreal.ToolMenuInsertType.FIRST)
        
        # Create toolbar button
        toolbar_button = unreal.ToolMenuEntry(type=unreal.MultiBlockType.TOOL_BAR_BUTTON, name="DreamwaveButton")
        toolbar_button.set_label("Dreamwave")
        toolbar_button.set_tool_tip("Dreamwave Texture Generator")
        toolbar_button.set_icon("EditorStyle", "LevelEditor.GameSettings")
        toolbar_button.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON, 
            string="import unreal; unreal.ToolMenus.get().invoke_menu_entry('LevelEditor.MainMenu.DreamwaveMenu.DreamwaveTexGen')", 
            custom_type=""
        )
        
        # Add the button to the toolbar section
        toolbar_extension.add_menu_entry("Dreamwave", toolbar_button)
        
        # Refresh all menus
        menus.refresh_all_widgets()
        unreal.log("Successfully registered Dreamwave menu and toolbar button")
        return True
    except Exception as e:
        unreal.log_error(f"Failed to register Dreamwave toolbar button: {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Alternative approach - try registering using a different method
def register_dreamwave_toolbar_alt():
    """Alternative method to register toolbar button using another extension point.
    
    This is a fallback method that:
    1. Registers a Dreamwave menu in the Window menu
    2. Adds three sub-menu items to it
    3. Uses the Actors toolbar extension point to add a Dreamwave button
    
    This method is tried if the primary method fails.
    """
    try:
        unreal.log("Attempting alternative toolbar registration method...")
        
        # Get ToolMenus
        menus = unreal.ToolMenus.get()
        if not menus:
            unreal.log_error("Failed to get ToolMenus instance")
            return False
        
        # Register Dreamwave Menu first (for dropdown items)
        dreamwave_menu = menus.register_menu(
            name="DreamwaveMenu", 
            display_name="Dreamwave", 
            parent_name="LevelEditor.MainMenu.Window"
        )
        
        if not dreamwave_menu:
            unreal.log_error("Failed to register Dreamwave menu")
            return False
            
        # Add a section to the menu
        dreamwave_menu.add_section("DreamwaveCommands", "Dreamwave")
        
        # Add menu items to the dropdown
        # 1. Texture Generator entry
        texgen_entry = unreal.ToolMenuEntry(type=unreal.MultiBlockType.MENU_ENTRY, name="DreamwaveTexGen")
        texgen_entry.set_label("Texture Generator")
        texgen_entry.set_tool_tip("Open Dreamwave Texture Generator")
        texgen_entry.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON, 
            string="import dreamwave_command; dreamwave_command.run_dreamwave()",
            custom_type=""
        )
        dreamwave_menu.add_menu_entry("DreamwaveCommands", texgen_entry)
        
        # 2. Launch ComfyUI entry
        launch_entry = unreal.ToolMenuEntry(type=unreal.MultiBlockType.MENU_ENTRY, name="DreamwaveLaunchComfyUI")
        launch_entry.set_label("Launch ComfyUI Server")
        launch_entry.set_tool_tip("Start the ComfyUI backend server")
        launch_entry.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON,
            string="import dreamwave_command; dreamwave_command.launch_comfyui()",
            custom_type=""
        )
        dreamwave_menu.add_menu_entry("DreamwaveCommands", launch_entry)
        
        # 3. Check Status entry
        status_entry = unreal.ToolMenuEntry(type=unreal.MultiBlockType.MENU_ENTRY, name="DreamwaveCheckStatus")
        status_entry.set_label("Check ComfyUI Status")
        status_entry.set_tool_tip("Check if ComfyUI server is running")
        status_entry.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON,
            string="import dreamwave_command; dreamwave_command.check_comfyui()",
            custom_type=""
        )
        dreamwave_menu.add_menu_entry("DreamwaveCommands", status_entry)
        
        # Now try to add a toolbar button using extension points
        menus.register_menu_extension_point(
            extension_hook="LevelEditor.ActorsToolBar",
            extension_point=unreal.ToolMenuExtensionPoint(
                extension_hook="LevelEditor.ActorsToolBar.ActorsToolBarExtensions"
            )
        )
        
        # Create toolbar extension
        toolbar_ext = menus.extend_menu("LevelEditor.ActorsToolBar")
        if not toolbar_ext:
            unreal.log_error("Failed to extend actors toolbar")
            return False
            
        # Add our section
        toolbar_ext.add_section("Dreamwave", "Dreamwave")
        
        # Create toolbar button
        toolbar_button = unreal.ToolMenuEntry(type=unreal.MultiBlockType.TOOL_BAR_BUTTON, name="DreamwaveButton")
        toolbar_button.set_label("Dreamwave")
        toolbar_button.set_tool_tip("Dreamwave Texture Generator")
        toolbar_button.set_icon("EditorStyle", "LevelEditor.GameSettings")
        toolbar_button.set_string_command(
            type=unreal.ToolMenuStringCommandType.PYTHON, 
            string="import dreamwave_command; dreamwave_command.run_dreamwave()", 
            custom_type=""
        )
        
        # Add the button to the toolbar section
        toolbar_ext.add_menu_entry("Dreamwave", toolbar_button)
        
        # Refresh all menus
        menus.refresh_all_widgets()
        unreal.log("Successfully registered Dreamwave menu and toolbar button (alt method)")
        return True
    except Exception as e:
        unreal.log_error(f"Failed to register Dreamwave toolbar button (alt method): {str(e)}")
        unreal.log_error(traceback.format_exc())
        return False

# Register the command
try:
    if register_dreamwave_command():
        unreal.log("Successfully registered 'dreamwave' command")
    else:
        unreal.log_error("Failed to register 'dreamwave' command")
except Exception as cmd_err:
    unreal.log_error(f"Error registering command: {str(cmd_err)}")

# Try to register the toolbar with the primary method
try:
    if register_dreamwave_toolbar():
        unreal.log("Successfully registered Dreamwave toolbar button")
    else:
        unreal.log("Primary toolbar registration failed, trying alternative method...")
        # Try the alternative method if the primary method fails
        if register_dreamwave_toolbar_alt():
            unreal.log("Successfully registered Dreamwave toolbar button with alternative method")
        else:
            unreal.log_error("Both toolbar registration methods failed")
except Exception as toolbar_err:
    unreal.log_error(f"Error registering toolbar button: {str(toolbar_err)}") 