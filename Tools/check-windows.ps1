# Read-only Sprint 0 prerequisite check. Does not fetch, install, or launch anything.
# Usage: powershell -NoProfile -ExecutionPolicy Bypass -File Tools\check-windows.ps1
# ExecutionPolicy applies only to this PowerShell process; no machine policy is changed.
param(
    [string]$EngineRoot = $(if ($env:UE_ROOT) { $env:UE_ROOT } else { 'C:\Program Files\Epic Games\UE_5.8' })
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$requiredVersion = '5.8.3'
$script:problems = 0

function Write-Check {
    param([bool]$Passed, [string]$Message, [string]$Fix)
    if ($Passed) {
        Write-Host "  OK    $Message"
    } else {
        $script:problems++
        Write-Host "  FIX   $Message"
        if ($Fix) { Write-Host "        $Fix" }
    }
}

Write-Host 'Co-op Game Windows prerequisites (HC-0)'
$versionFile = Join-Path $EngineRoot 'Engine\Build\Build.version'
if (Test-Path -LiteralPath $versionFile) {
    try {
        $buildVersion = Get-Content -LiteralPath $versionFile -Raw | ConvertFrom-Json
        $installedVersion = '{0}.{1}.{2}' -f $buildVersion.MajorVersion, $buildVersion.MinorVersion, $buildVersion.PatchVersion
        Write-Check ($installedVersion -eq $requiredVersion) "Unreal $installedVersion; team requires $requiredVersion" 'Update Unreal in the Epic Games Launcher before creating or saving project assets.'
    } catch {
        Write-Check $false 'Cannot read the installed Unreal version.' 'Check the engine installation and UE_ROOT.'
    }
} else {
    Write-Check $false "Unreal $requiredVersion not found at $EngineRoot" 'Install the required engine or set UE_ROOT to its installation folder.'
}

Write-Check (Test-Path -LiteralPath (Join-Path $EngineRoot 'Engine\Binaries\Win64\UnrealEditor.exe')) 'Unreal Editor executable' 'Verify the engine installation in the Epic Games Launcher.'
foreach ($template in @('TP_ThirdPersonBP', 'TP_VehicleAdvBP')) {
    Write-Check (Test-Path -LiteralPath (Join-Path $EngineRoot "Templates\$template\$template.uproject")) "$template template" 'Install Templates and Feature Packs using the engine installation options.'
}

foreach ($plugin in @('ModelContextProtocol', 'Toolsets\AllToolsets', 'ChaosVehiclesPlugin', 'PythonScriptPlugin')) {
    $pluginName = Split-Path -Leaf $plugin
    $descriptor = Join-Path $EngineRoot "Engine\Plugins\Experimental\$plugin\$pluginName.uplugin"
    Write-Check (Test-Path -LiteralPath $descriptor) "$pluginName plugin installed (not yet checked as enabled)" 'Verify the engine installation.'
}

if (Get-Command git -ErrorAction SilentlyContinue) {
    $gitVersion = & git --version
    Write-Check ($LASTEXITCODE -eq 0) $gitVersion 'Install Git for Windows.'
    $lfsVersion = & git lfs version 2>$null
    Write-Check ($LASTEXITCODE -eq 0) "Git LFS: $lfsVersion" 'Install Git LFS.'
    $lfsFilter = & git -C $repoRoot config --get filter.lfs.process
    Write-Check (($LASTEXITCODE -eq 0) -and ($lfsFilter -eq 'git-lfs filter-process')) 'Git LFS configured for this checkout' 'Run git lfs install --local from the repository root.'
    $gitRoot = & git -C $repoRoot rev-parse --show-toplevel
    Write-Check ($LASTEXITCODE -eq 0) "Repository: $gitRoot" 'Clone the repository before starting HC-0.'
} else {
    Write-Check $false 'Git not found.' 'Install Git for Windows.'
}

# The engine is already installed; reserve the same 30 GB working margin as the Mac check.
$driveRoot = [System.IO.Path]::GetPathRoot($repoRoot)
$drive = [System.IO.DriveInfo]::new($driveRoot)
$freeGB = [math]::Round($drive.AvailableFreeSpace / 1GB, 1)
Write-Check ($freeGB -ge 30) "$freeGB GB free on the project drive" 'Free at least 30 GB for project assets and shader caches.'

if (Test-Path -LiteralPath (Join-Path $repoRoot 'CoopGame.uproject')) {
    Write-Host '  NOTE  CoopGame exists; editor setup and multiplayer still need verification.'
} else {
    Write-Host '  NOTE  CoopGame has not been created yet; this is HC-0 work.'
}

if ($script:problems -gt 0) {
    Write-Host "Prerequisite check failed: $script:problems item(s) to fix."
    exit 1
}
Write-Host 'Prerequisites passed. This does not verify editor setup or Playable 1.'
exit 0
