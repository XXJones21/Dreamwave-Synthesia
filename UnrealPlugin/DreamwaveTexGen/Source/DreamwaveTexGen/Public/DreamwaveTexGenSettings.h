// Copyright Dreamwave Synthesia. All Rights Reserved.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "DreamwaveTexGenSettings.generated.h"

/**
 * Settings for the Dreamwave Texture Generator
 */
UCLASS(config=Editor, defaultconfig)
class DREAMWAVETEXGEN_API UDreamwaveTexGenSettings : public UObject
{
	GENERATED_BODY()
	
public:
	UDreamwaveTexGenSettings(const FObjectInitializer& ObjectInitializer);

	/** ComfyUI server address */
	UPROPERTY(config, EditAnywhere, Category = "Server", meta = (DisplayName = "ComfyUI Server URL"))
	FString ComfyUIServerURL;
	
	/** Path to the ComfyUI workflow file */
	UPROPERTY(config, EditAnywhere, Category = "Workflow", meta = (DisplayName = "Workflow File Path", FilePathFilter = "JSON Files (*.json)|*.json"))
	FFilePath WorkflowFilePath;
	
	/** Default output directory for generated textures */
	UPROPERTY(config, EditAnywhere, Category = "Output", meta = (DisplayName = "Default Output Directory", RelativeToGameContentDir))
	FDirectoryPath DefaultOutputDirectory;
	
	/** Default texture resolution */
	UPROPERTY(config, EditAnywhere, Category = "Texture", meta = (DisplayName = "Default Resolution", ClampMin = "256", ClampMax = "4096", UIMin = "256", UIMax = "4096"))
	int32 DefaultResolution;
	
	/** Default texture type */
	UPROPERTY(config, EditAnywhere, Category = "Texture", meta = (DisplayName = "Default Texture Type"))
	TEnumAsByte<enum ETextureSourceFormat> DefaultTextureType;
	
	/** Style presets for quick generation */
	UPROPERTY(config, EditAnywhere, Category = "Presets", meta = (DisplayName = "Style Presets"))
	TArray<FString> StylePresets;
}; 