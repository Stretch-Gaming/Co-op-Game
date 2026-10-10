# Synthetic fixtures only. Never starts Unreal or modifies project maps.
$ErrorActionPreference='Stop'
$fixture=Join-Path ([IO.Path]::GetTempPath()) ('Co op launcher test '+[guid]::NewGuid())
$oldEngine=$env:UE_ROOT
$tests=0
try {
 $tools=Join-Path $fixture 'Tools'
 $helper=Join-Path $tools 'launch_preview'
 $maps=Join-Path $fixture 'Content/Maps'
 $adventure=Join-Path $fixture 'Content/Puzzles/Test/SixRound'
 $engine=Join-Path $fixture 'Engine install with spaces'
 $build=Join-Path $engine 'Engine/Build/Build.version'
 New-Item -ItemType Directory -Force $helper,$maps,$adventure,(Split-Path $build),(Join-Path $engine 'Engine/Binaries/Win64') | Out-Null
 Copy-Item -LiteralPath "$PSScriptRoot/launch.ps1" -Destination $helper
 Copy-Item -LiteralPath "$PSScriptRoot/../host.bat","$PSScriptRoot/../play-connected.bat","$PSScriptRoot/../play-adventure.bat" -Destination $tools
 Set-Content -LiteralPath "$fixture/CoopGame.uproject" -Value '{}'
 foreach ($name in 'L_Site01','L_ConnectedRoomMaze') { Set-Content -LiteralPath "$maps/$name.umap" -Value 'synthetic map fixture' }
 Set-Content -LiteralPath "$adventure/L_SixRound_Test.umap" -Value 'synthetic adventure map fixture'
 Set-Content -LiteralPath "$engine/Engine/Binaries/Win64/UnrealEditor.exe" -Value 'never executed'
 Set-Content -LiteralPath $build -Value '{"MajorVersion":5,"MinorVersion":8,"PatchVersion":3}'
 $env:UE_ROOT=$engine
 function Check([string]$Script,[string]$Options,[int]$Code,[string[]]$Contains,[string[]]$Absent=@()) {
  $wrapper=Join-Path $tools $Script
  $output=(& $env:ComSpec /d /c "call `"$wrapper`" $Options" 2>&1 | Out-String)
  if ($LASTEXITCODE -ne $Code) { throw "Wrong exit for $Script $Options : $output" }
  foreach ($text in $Contains) { if (!$output.Contains($text)) { throw "Missing $text : $output" } }
  foreach ($text in $Absent) { if ($output.Contains($text)) { throw "Unexpected $text : $output" } }
  $script:tests++
 }
 Check 'play-connected.bat' '--dry-run' 0 @("ARG: $fixture\CoopGame.uproject",'/Game/Maps/L_ConnectedRoomMaze','-DisablePython','-d3d11','-noraytracing','at commit unknown') @('?listen')
 Check 'host.bat' '--dry-run' 0 @('/Game/Puzzles/Test/SixRound/L_SixRound_Test?listen','-DisablePython') @('-d3d11','-noraytracing')
 Check 'play-adventure.bat' '--dry-run' 0 @("ARG: $fixture\CoopGame.uproject",'/Game/Puzzles/Test/SixRound/L_SixRound_Test?listen','-DisablePython') @('-d3d11','-noraytracing')
 Check 'play-adventure.bat' '/Game/Maps/L_Site01 --dry-run' 1 @('Usage:')
 Check 'host.bat' '/Game/Maps/L_ConnectedRoomMaze --dry-run' 0 @('/Game/Maps/L_ConnectedRoomMaze?listen')
 Check 'host.bat' '--dry-run /Game/Maps/L_ConnectedRoomMaze' 0 @('/Game/Maps/L_ConnectedRoomMaze?listen')
 Check 'host.bat' '/Game/Maps/Missing --dry-run' 1 @('Map missing:')
 Check 'host.bat' '/Game/../Maps/L_Site01 --dry-run' 1 @('Usage:')
 Check 'host.bat' '/Game/Maps/L_Site01?listen --dry-run' 1 @('Usage:')
 Check 'play-connected.bat' '/Game/Maps/L_Site01 --dry-run' 1 @('Usage:')
 Set-Content -LiteralPath "$maps/L_ConnectedRoomMaze.umap" -Value 'version https://git-lfs.github.com/spec/v1'
 Check 'play-connected.bat' '--dry-run' 1 @('Git LFS pointer:','git lfs pull')
 Set-Content -LiteralPath "$adventure/L_SixRound_Test.umap" -Value 'version https://git-lfs.github.com/spec/v1'
 Check 'host.bat' '--dry-run' 1 @('Git LFS pointer:')
 Check 'play-adventure.bat' '--dry-run' 1 @('Git LFS pointer:')
 Set-Content -LiteralPath "$adventure/L_SixRound_Test.umap" -Value 'synthetic adventure map fixture'
 Set-Content -LiteralPath $build -Value '{"MajorVersion":5,"MinorVersion":8,"PatchVersion":2}'
 Check 'host.bat' '--dry-run' 1 @('requires 5.8.3')
 $env:UE_ROOT=Join-Path $fixture 'Missing engine'
 Check 'host.bat' '--dry-run' 1 @('Unreal 5.8.3 not found')
 Write-Host "PASS: $tests Windows launcher checks; no engine launched."
} finally {
 $env:UE_ROOT=$oldEngine
 # Remove only this uniquely named fixture under the resolved temporary directory.
 $resolved=[IO.Path]::GetFullPath($fixture)
 $tempRoot=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
 if (!$resolved.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase)) { throw 'Fixture escaped temporary directory.' }
 if (Test-Path -LiteralPath $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}
