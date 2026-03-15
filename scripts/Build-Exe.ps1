[CmdletBinding()]
param(
    [string]$Name = "CampfireSandwich",
    [switch]$OneFile,
    [switch]$NoInstall,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-PythonLauncher {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        return @("py", "-3")
    }

    if (Get-Command python -ErrorAction SilentlyContinue) {
        return @("python")
    }

    throw "Python was not found on PATH. Install Python 3 and try again."
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]
        [string[]]$Args
    )

    $launcher = @(Get-PythonLauncher)
    $exe = $launcher[0]
    $prefix = @()
    if ($launcher.Count -gt 1) {
        $prefix = $launcher[1..($launcher.Count - 1)]
    }

    & $exe @prefix @Args
}

$scriptDir = Split-Path -Parent $PSCommandPath
$repoRoot = Split-Path -Parent $scriptDir
$entryPoint = Join-Path $repoRoot "src/main.py"

if (-not (Test-Path $entryPoint)) {
    throw "Entry point not found at $entryPoint"
}

$assetDirs = @("art", "fonts", "music", "sfx", "sprites")
$addDataArgs = @()

foreach ($dir in $assetDirs) {
    $abs = Join-Path $repoRoot $dir
    if (Test-Path $abs) {
        $addDataArgs += "--add-data"
        $addDataArgs += "$abs;$dir"
    }
}

$pyiArgs = @(
    "-m", "PyInstaller",
    "--noconfirm",
    "--clean",
    "--windowed",
    "--name", $Name,
    "--distpath", (Join-Path $repoRoot "dist"),
    "--workpath", (Join-Path $repoRoot "build/pyinstaller")
)

if ($OneFile) {
    $pyiArgs += "--onefile"
}

$pyiArgs += $addDataArgs
$pyiArgs += $entryPoint

Push-Location $repoRoot
try {
    if (-not $NoInstall) {
        Write-Host "Checking PyInstaller..."
        try {
            Invoke-Python -Args @("-m", "PyInstaller", "--version") | Out-Null
        }
        catch {
            Write-Host "PyInstaller not found. Installing with pip..."
            Invoke-Python -Args @("-m", "pip", "install", "pyinstaller")
        }
    }

    if ($DryRun) {
        $preview = @(Get-PythonLauncher) + $pyiArgs
        Write-Host "Dry run command:"
        Write-Host ($preview -join " ")
        return
    }

    Write-Host "Building executable..."
    Invoke-Python -Args $pyiArgs

    $outDir = Join-Path $repoRoot "dist/$Name"
    $outExe = Join-Path $outDir "$Name.exe"
    $oneFileExe = Join-Path $repoRoot "dist/$Name.exe"

    if (Test-Path $outExe) {
        Write-Host "Build complete: $outExe"
    }
    elseif (Test-Path $oneFileExe) {
        Write-Host "Build complete: $oneFileExe"
    }
    else {
        Write-Warning "PyInstaller finished, but the expected exe path was not found. Check the dist folder."
    }
}
finally {
    Pop-Location
}
