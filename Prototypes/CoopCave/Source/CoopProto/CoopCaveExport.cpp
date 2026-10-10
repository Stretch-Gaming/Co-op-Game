#include "CoopPlayground.h"

#include "Components/BoxComponent.h"
#include "Components/DirectionalLightComponent.h"
#include "Components/ExponentialHeightFogComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SkyLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Dom/JsonObject.h"
#include "Engine/PostProcessVolume.h"
#include "Engine/StaticMesh.h"
#include "EngineUtils.h"
#include "HAL/FileManager.h"
#include "HAL/IConsoleManager.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "ProceduralMeshComponent.h"
#include "Serialization/JsonSerializer.h"

namespace CoopCaveTransfer
{
	TArray<TSharedPtr<FJsonValue>> Numbers(std::initializer_list<double> Values)
	{
		TArray<TSharedPtr<FJsonValue>> Result;
		for (double Value : Values) { Result.Add(MakeShared<FJsonValueNumber>(Value)); }
		return Result;
	}

	TSharedPtr<FJsonObject> ComponentRecord(USceneComponent* Component)
	{
		TSharedPtr<FJsonObject> Record = MakeShared<FJsonObject>();
		const FTransform Transform = Component->GetComponentTransform();
		const FVector P = Transform.GetLocation();
		const FRotator R = Transform.Rotator();
		const FVector S = Transform.GetScale3D();
		Record->SetStringField(TEXT("name"), Component->GetName());
		Record->SetArrayField(TEXT("location"), Numbers({P.X, P.Y, P.Z}));
		Record->SetArrayField(TEXT("rotation"), Numbers({R.Pitch, R.Yaw, R.Roll}));
		Record->SetArrayField(TEXT("scale"), Numbers({S.X, S.Y, S.Z}));
		return Record;
	}

	void AddMaterial(UMeshComponent* Component, TSharedPtr<FJsonObject> Record)
	{
		FLinearColor Color = FLinearColor::White;
		UMaterialInterface* Material = Component->GetMaterial(0);
		if (UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Material))
		{
			Color = Dynamic->K2_GetVectorParameterValue(TEXT("Color"));
		}
		Record->SetArrayField(TEXT("color"), Numbers({Color.R, Color.G, Color.B, Color.A}));
		Record->SetBoolField(TEXT("glow"), Material && Material->GetName().Contains(TEXT("VertexColor")));
		Record->SetBoolField(TEXT("collision"), Component->GetCollisionEnabled() != ECollisionEnabled::NoCollision);
		Record->SetBoolField(TEXT("shadow"), Component->CastShadow);
	}

	void Export(UWorld* World)
	{
		TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
		TArray<TSharedPtr<FJsonValue>> Records;
		for (TActorIterator<ACoopPlayground> It(World); It; ++It)
		{
			TArray<USceneComponent*> Components;
			It->GetComponents<USceneComponent>(Components);
			for (USceneComponent* Component : Components)
			{
				TSharedPtr<FJsonObject> Record = ComponentRecord(Component);
				if (UStaticMeshComponent* Static = Cast<UStaticMeshComponent>(Component))
				{
					if (!Static->GetStaticMesh()) { continue; }
					Record->SetStringField(TEXT("kind"), TEXT("static"));
					Record->SetStringField(TEXT("mesh"), Static->GetStaticMesh()->GetPathName());
					AddMaterial(Static, Record);
				}
				else if (UProceduralMeshComponent* Proc = Cast<UProceduralMeshComponent>(Component))
				{
					const FProcMeshSection* Section = Proc->GetProcMeshSection(0);
					if (!Section) { continue; }
					Record->SetStringField(TEXT("kind"), TEXT("procedural"));
					AddMaterial(Proc, Record);
					TArray<TSharedPtr<FJsonValue>> Vertices, Normals, UVs, Colors, Triangles;
					for (const FProcMeshVertex& Vertex : Section->ProcVertexBuffer)
					{
						Vertices.Add(MakeShared<FJsonValueArray>(Numbers({Vertex.Position.X, Vertex.Position.Y, Vertex.Position.Z})));
						Normals.Add(MakeShared<FJsonValueArray>(Numbers({Vertex.Normal.X, Vertex.Normal.Y, Vertex.Normal.Z})));
						UVs.Add(MakeShared<FJsonValueArray>(Numbers({Vertex.UV0.X, Vertex.UV0.Y})));
						const FLinearColor C = FLinearColor::FromSRGBColor(Vertex.Color);
						Colors.Add(MakeShared<FJsonValueArray>(Numbers({C.R, C.G, C.B, C.A})));
					}
					for (uint32 Index : Section->ProcIndexBuffer) { Triangles.Add(MakeShared<FJsonValueNumber>(Index)); }
					Record->SetArrayField(TEXT("vertices"), Vertices);
					Record->SetArrayField(TEXT("normals"), Normals);
					Record->SetArrayField(TEXT("uvs"), UVs);
					Record->SetArrayField(TEXT("vertex_colors"), Colors);
					Record->SetArrayField(TEXT("triangles"), Triangles);
				}
				else if (UBoxComponent* Box = Cast<UBoxComponent>(Component))
				{
					Record->SetStringField(TEXT("kind"), TEXT("blocker"));
					const FVector Extent = Box->GetUnscaledBoxExtent();
					Record->SetArrayField(TEXT("extent"), Numbers({Extent.X, Extent.Y, Extent.Z}));
				}
				else if (UPointLightComponent* Light = Cast<UPointLightComponent>(Component))
				{
					Record->SetStringField(TEXT("kind"), TEXT("point"));
					Record->SetNumberField(TEXT("intensity"), Light->Intensity);
					Record->SetNumberField(TEXT("radius"), Light->AttenuationRadius);
					Record->SetBoolField(TEXT("shadow"), Light->CastShadows);
					const FLinearColor C = Light->GetLightColor();
					Record->SetArrayField(TEXT("color"), Numbers({C.R, C.G, C.B, C.A}));
				}
				else { continue; }
				Records.Add(MakeShared<FJsonValueObject>(Record));
			}
		}
		Root->SetArrayField(TEXT("components"), Records);
		Root->SetNumberField(TEXT("seed"), 2610);
		Root->SetStringField(TEXT("source"), TEXT("CoopCave procedural environment only; no character or gameplay code"));
		FString Json;
		FJsonSerializer::Serialize(Root.ToSharedRef(), TJsonWriterFactory<>::Create(&Json));
		const FString Directory = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("CaveTransfer"));
		IFileManager::Get().MakeDirectory(*Directory, true);
		const FString Filename = FPaths::Combine(Directory, TEXT("cave.json"));
		if (!Records.IsEmpty() && FFileHelper::SaveStringToFile(Json, *Filename, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM))
		{
			UE_LOG(LogTemp, Display, TEXT("CAVE_EXPORT_COMPLETE: %d components to %s"), Records.Num(), *Filename);
		}
		else { UE_LOG(LogTemp, Error, TEXT("Cave export failed or no playground was loaded")); }
	}

	FAutoConsoleCommandWithWorld Command(TEXT("coop.ExportCave"), TEXT("Export cave geometry and lights for editor baking into CoopGame."), FConsoleCommandWithWorldDelegate::CreateStatic(&Export));
}
