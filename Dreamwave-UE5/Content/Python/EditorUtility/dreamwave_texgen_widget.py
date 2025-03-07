"""
Dreamwave Texture Generator - Editor Utility Widget
This script creates an Editor Utility Widget for the Dreamwave Texture Generator.
"""

import unreal
import os
import sys

def create_editor_utility_widget():
    """Create an Editor Utility Widget for the Dreamwave Texture Generator."""
    
    # Create the asset
    asset_name = "DreamwaveTexGenWidget"
    asset_path = "/Game/DreamwaveTexGen"
    full_path = f"{asset_path}/{asset_name}"
    
    # Create the package and asset
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.make_directory(asset_path)
    
    # Check if the asset already exists
    if unreal.EditorAssetLibrary.does_asset_exist(full_path):
        unreal.log(f"Editor Utility Widget already exists at {full_path}")
        return full_path
    
    # Create the EditorUtilityWidgetBlueprint
    factory = unreal.EditorUtilityWidgetBlueprintFactory()
    factory.set_editor_property("parent_class", unreal.EditorUtilityWidget.static_class())
    
    # Create the asset
    new_asset = asset_tools.create_asset(asset_name, asset_path, unreal.EditorUtilityWidgetBlueprint, factory)
    if not new_asset:
        unreal.log_error(f"Failed to create Editor Utility Widget at {full_path}")
        return None
    
    # Get the generated widget class
    widget_class = new_asset.generated_class()
    
    # Modify the blueprint to add our custom UI
    blueprint = unreal.EditorLoadingAndSavingUtils.get_blueprint_asset_from_path(full_path)
    if not blueprint:
        unreal.log_error(f"Failed to load blueprint asset from {full_path}")
        return None
    
    # Add custom UI elements
    with unreal.ScopedEditorTransaction("Modify Dreamwave Widget") as trans:
        # Get the widget tree
        widget_tree = blueprint.get_editor_property("widget_tree")
        if not widget_tree:
            unreal.log_error("Failed to get widget tree")
            return None
        
        # Get the root widget
        root_widget = widget_tree.get_editor_property("root_widget")
        if not root_widget:
            unreal.log_error("Failed to get root widget")
            return None
        
        # Create a vertical box as the main container
        vertical_box = unreal.WidgetBlueprintLib.create_widget(blueprint, unreal.VerticalBox.static_class())
        widget_tree.set_editor_property("root_widget", vertical_box)
        
        # Add a title text block
        title = unreal.WidgetBlueprintLib.create_widget(blueprint, unreal.TextBlock.static_class())
        title.set_editor_property("text", unreal.Text("Dreamwave Texture Generator"))
        title.set_editor_property("justification", unreal.TextJustify.CENTER)
        title.set_editor_property("font_size", 24)
        vertical_box.add_child(title)
        
        # Add a button to open the texture generator
        button = unreal.WidgetBlueprintLib.create_widget(blueprint, unreal.Button.static_class())
        button_text = unreal.WidgetBlueprintLib.create_widget(blueprint, unreal.TextBlock.static_class())
        button_text.set_editor_property("text", unreal.Text("Open Texture Generator"))
        button.set_editor_property("content", button_text)
        vertical_box.add_child(button)
        
        # Add Python script to the button click event
        script = """
import unreal
import sys
import os

# Add plugin path to sys.path
plugin_path = os.path.join(unreal.Paths.project_plugins_dir(), "DreamwaveTexGen", "Content", "Python")
if plugin_path not in sys.path:
    sys.path.append(plugin_path)

try:
    # Import the modules
    from dreamwave_texgen_api import DreamwaveTexGenAPI
    import dreamwave_texgen_ui
    
    # Create API and show UI
    api = DreamwaveTexGenAPI()
    dreamwave_texgen_ui.show_ui(api)
    
    unreal.log("Dreamwave Texture Generator UI opened")
except Exception as e:
    unreal.log_error(f"Failed to open Texture Generator: {str(e)}")
    unreal.EditorDialog.show_message(
        title="Dreamwave Texture Generator Error",
        message=f"Error: {str(e)}\\n\\nPlease check the Output Log for details.",
        dialog_type=unreal.AppMsgType.OK
    )
"""
        
        # Create a Python script object
        script_asset_path = f"{asset_path}/OpenTexGenScript"
        if not unreal.EditorAssetLibrary.does_asset_exist(script_asset_path):
            script_factory = unreal.PythonScriptFactory()
            script_asset = asset_tools.create_asset("OpenTexGenScript", asset_path, unreal.PythonScript, script_factory)
            if script_asset:
                script_asset.set_editor_property("script", script)
                unreal.EditorAssetLibrary.save_asset(script_asset_path)
        
        # Add the button click event
        button.on_clicked.add_python_script(script)
    
    # Save the blueprint
    unreal.EditorLoadingAndSavingUtils.save_blueprint(blueprint)
    unreal.EditorAssetLibrary.save_asset(full_path)
    
    unreal.log(f"Created Editor Utility Widget at {full_path}")
    return full_path

def register_editor_utility_tab():
    """Register the Editor Utility Widget as a tab."""
    widget_path = create_editor_utility_widget()
    if not widget_path:
        unreal.log_error("Failed to create or find Editor Utility Widget")
        return
    
    # Register the tab
    blueprint = unreal.EditorAssetLibrary.load_asset(widget_path)
    if not blueprint:
        unreal.log_error(f"Failed to load asset at {widget_path}")
        return
    
    # Create the tab
    editor_utility_subsystem = unreal.get_editor_subsystem(unreal.EditorUtilitySubsystem)
    editor_utility_subsystem.register_tab_and_get_id(blueprint)
    unreal.log("Registered Dreamwave Texture Generator tab")

# Run the registration
if __name__ == "__main__":
    register_editor_utility_tab() 