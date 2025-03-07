// Copyright Dreamwave Synthesia. All Rights Reserved.

using UnrealBuildTool;
using System.IO;

public class DreamwaveTexGen : ModuleRules
{
	public DreamwaveTexGen(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = ModuleRules.PCHUsageMode.UseExplicitOrSharedPCHs;
		
		PublicIncludePaths.AddRange(
			new string[] {
				// ... add public include paths required here ...
			}
		);
				
		PrivateIncludePaths.AddRange(
			new string[] {
				// ... add other private include paths required here ...
			}
		);
			
		PublicDependencyModuleNames.AddRange(
			new string[]
			{
				"Core",
				"CoreUObject",
				"Engine",
				"InputCore",
				"Slate",
				"SlateCore",
				"EditorScriptingUtilities",
				"UMG",
				"HTTP",
				"Json",
				"JsonUtilities",
				"Projects",
				// ... add other public dependencies that you statically link with here ...
			}
		);
			
		PrivateDependencyModuleNames.AddRange(
			new string[]
			{
				"UnrealEd",
				"AssetTools",
				"ContentBrowser",
				"PythonScriptPlugin",
				"LevelEditor",
				"EditorStyle",
				"DesktopPlatform",
				// ... add private dependencies that you statically link with here ...	
			}
		);
		
		DynamicallyLoadedModuleNames.AddRange(
			new string[]
			{
				// ... add any modules that your module loads dynamically here ...
			}
		);
	}
} 