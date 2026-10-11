param(
 [Parameter(Mandatory=$true,Position=0)][ValidateSet('host','preview')][string]$Mode,
 [Parameter(ValueFromRemainingArguments=$true)][string[]]$LaunchOptions
)
$ErrorActionPreference='Stop'
try {
 $root=Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
 $map=if ($Mode -eq 'preview') { '/Game/Maps/L_ConnectedRoomMaze' } else { '/Game/Puzzles/Test/SixRound/L_SixRound_Test' }
 $dryRun=$false
 $mapGiven=$false
 foreach ($option in $LaunchOptions) {
  if ($option -eq '--dry-run' -and !$dryRun) { $dryRun=$true }
  elseif ($Mode -eq 'host' -and !$mapGiven -and $option -cmatch '^/Game/(?:[A-Za-z0-9_]+/)*[A-Za-z0-9_]+$') { $map=$option; $mapGiven=$true }
  else { throw 'Usage: host.bat [/Game/Maps/MapName] [--dry-run], or play-connected.bat [--dry-run]. Map names allow letters, numbers, underscores and slashes.' }
 }
 $project=Join-Path $root 'CoopGame.uproject'
 if (!(Test-Path -LiteralPath $project -PathType Leaf)) { throw "Project missing: $project. Pull the latest project first." }
 $mapFile=Join-Path $root ('Content/'+$map.Substring(6)+'.umap')
 if (!(Test-Path -LiteralPath $mapFile -PathType Leaf)) { throw "Map missing: $mapFile. Pull the latest project and run git lfs pull." }
 $stream=[System.IO.File]::OpenRead($mapFile)
 try {
  $prefix=New-Object byte[] 128
  $count=$stream.Read($prefix,0,$prefix.Length)
  if ([Text.Encoding]::ASCII.GetString($prefix,0,$count).StartsWith('version https://git-lfs.github.com/spec/v1')) { throw "Map is a Git LFS pointer: $mapFile. Run git lfs pull before playing." }
 } finally { $stream.Dispose() }
 $engineRoot=if ($env:UE_ROOT) { $env:UE_ROOT } else { 'C:\Program Files\Epic Games\UE_5.8' }
 $editor=Join-Path $engineRoot 'Engine/Binaries/Win64/UnrealEditor.exe'
 $versionFile=Join-Path $engineRoot 'Engine/Build/Build.version'
 if (!(Test-Path -LiteralPath $editor -PathType Leaf) -or !(Test-Path -LiteralPath $versionFile -PathType Leaf)) { throw "Unreal 5.8.3 not found at $engineRoot. Set UE_ROOT to your Unreal installation folder." }
 $version=Get-Content -LiteralPath $versionFile -Raw | ConvertFrom-Json
 $installed='{0}.{1}.{2}' -f $version.MajorVersion,$version.MinorVersion,$version.PatchVersion
 if ($installed -ne '5.8.3') { throw "Unreal $installed found; this project requires 5.8.3. Check UE_ROOT." }
 $mapUrl=if ($Mode -eq 'host') { $map+'?listen' } else { $map }
 $editorArgs=@($project,$mapUrl,'-game','-DisablePython','-windowed','-ResX=1280','-ResY=720','-log')
 if ($Mode -eq 'preview') { $editorArgs+=@('-d3d11','-noraytracing') }
 $commit='unknown'
 if (Get-Command git -ErrorAction SilentlyContinue) {
  try {
   $revision=& git -C $root rev-parse --short HEAD 2>&1
   if ($LASTEXITCODE -eq 0) { $commit=($revision | Select-Object -First 1).ToString() }
  } catch { $commit='unknown' }
 }
 Write-Host "Launching $Mode on $map with Unreal $installed at commit $commit"
 if ($dryRun) {
  Write-Output "EXE: $editor"
  $editorArgs | ForEach-Object { Write-Output "ARG: $_" }
  exit 0
 }
 if ($Mode -eq 'host') {
  Write-Host 'Players join with Tools\join.bat IP or Tools/join.command IP.'
  Write-Host 'Another player on this PC: Tools\join.bat 127.0.0.1.'
  Write-Host 'Allow Unreal Editor through Windows Firewall on private networks if needed.'
  ipconfig | Select-String 'IPv4' | ForEach-Object { Write-Host $_ }
 }
 # Quote each argument so project and engine paths may contain spaces.
 Start-Process -FilePath $editor -ArgumentList (($editorArgs | ForEach-Object { '"'+$_+'"' }) -join ' ')
 exit 0
} catch {
 Write-Host "ERROR: $($_.Exception.Message)"
 exit 1
}
