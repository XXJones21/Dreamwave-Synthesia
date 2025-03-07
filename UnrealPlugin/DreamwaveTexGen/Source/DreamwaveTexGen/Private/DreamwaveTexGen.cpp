// Copyright Dreamwave Synthesia. All Rights Reserved.

#include "DreamwaveTexGen.h"
#include "DreamwaveTexGenStyle.h"
#include "DreamwaveTexGenCommands.h"
#include "DreamwaveTexGenUI.h"
#include "LevelEditor.h"
#include "Widgets/Docking/SDockTab.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "ToolMenus.h"
#include "ISettingsModule.h"
#include "ISettingsSection.h"
#include "DreamwaveTexGenSettings.h"

static const FName DreamwaveTexGenTabName("DreamwaveTexGen");

#define LOCTEXT_NAMESPACE "FDreamwaveTexGenModule"

void FDreamwaveTexGenModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	
	FDreamwaveTexGenStyle::Initialize();
	FDreamwaveTexGenStyle::ReloadTextures();

	FDreamwaveTexGenCommands::Register();
	
	PluginCommands = MakeShareable(new FUICommandList);

	PluginCommands->MapAction(
		FDreamwaveTexGenCommands::Get().OpenPluginWindow,
		FExecuteAction::CreateRaw(this, &FDreamwaveTexGenModule::PluginButtonClicked),
		FCanExecuteAction());

	UToolMenus::RegisterStartupCallback(FSimpleMulticastDelegate::FDelegate::CreateRaw(this, &FDreamwaveTexGenModule::RegisterMenus));
	
	FGlobalTabmanager::Get()->RegisterNomadTabSpawner(DreamwaveTexGenTabName, FOnSpawnTab::CreateRaw(this, &FDreamwaveTexGenModule::OnSpawnPluginTab))
		.SetDisplayName(LOCTEXT("FDreamwaveTexGenTabTitle", "Dreamwave Texture Generator"))
		.SetMenuType(ETabSpawnerMenuType::Hidden);
	
	// Register settings
	ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings");
	if (SettingsModule)
	{
		ISettingsSectionPtr SettingsSection = SettingsModule->RegisterSettings("Project", "Plugins", "DreamwaveTexGen",
			LOCTEXT("DreamwaveTexGenSettingsName", "Dreamwave Texture Generator"),
			LOCTEXT("DreamwaveTexGenSettingsDescription", "Configure the Dreamwave Texture Generator plugin"),
			GetMutableDefault<UDreamwaveTexGenSettings>()
		);
	}
}

void FDreamwaveTexGenModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

	UToolMenus::UnRegisterStartupCallback(this);

	UToolMenus::UnregisterOwner(this);

	FDreamwaveTexGenStyle::Shutdown();

	FDreamwaveTexGenCommands::Unregister();

	FGlobalTabmanager::Get()->UnregisterNomadTabSpawner(DreamwaveTexGenTabName);
	
	// Unregister settings
	ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings");
	if (SettingsModule)
	{
		SettingsModule->UnregisterSettings("Project", "Plugins", "DreamwaveTexGen");
	}
}

TSharedRef<SDockTab> FDreamwaveTexGenModule::OnSpawnPluginTab(const FSpawnTabArgs& SpawnTabArgs)
{
	return SNew(SDockTab)
		.TabRole(ETabRole::NomadTab)
		[
			SNew(SDreamwaveTexGenUI)
		];
}

void FDreamwaveTexGenModule::PluginButtonClicked()
{
	FGlobalTabmanager::Get()->TryInvokeTab(DreamwaveTexGenTabName);
}

void FDreamwaveTexGenModule::RegisterMenus()
{
	// Owner will be used for cleanup in call to UToolMenus::UnregisterOwner
	FToolMenuOwnerScoped OwnerScoped(this);

	{
		UToolMenu* Menu = UToolMenus::Get()->ExtendMenu("LevelEditor.MainMenu.Tools");
		{
			FToolMenuSection& Section = Menu->FindOrAddSection("Content");
			Section.AddMenuEntryWithCommandList(FDreamwaveTexGenCommands::Get().OpenPluginWindow, PluginCommands);
		}
	}

	{
		UToolMenu* ToolbarMenu = UToolMenus::Get()->ExtendMenu("LevelEditor.LevelEditorToolBar");
		{
			FToolMenuSection& Section = ToolbarMenu->FindOrAddSection("Content");
			{
				FToolMenuEntry& Entry = Section.AddEntry(FToolMenuEntry::InitToolBarButton(FDreamwaveTexGenCommands::Get().OpenPluginWindow));
				Entry.SetCommandList(PluginCommands);
			}
		}
	}
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FDreamwaveTexGenModule, DreamwaveTexGen) 