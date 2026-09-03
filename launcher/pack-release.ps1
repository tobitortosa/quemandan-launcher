# Arma el instalador del launcher y lo publica como release del repositorio.
#
#   pwsh ./pack-release.ps1 -Version 1.0.0
#
# Deja en releases/ un Setup.exe para el que instala por primera vez, y los archivos
# que el launcher ya instalado usa para actualizarse solo.

param(
  [Parameter(Mandatory = $true)][string]$Version,
  [string]$Channel = "win",
  [switch]$Publish
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$project = Join-Path $root "src/QueMandan.App/QueMandan.App.csproj"
$publishDir = Join-Path $root "artifacts/publish"
$releaseDir = Join-Path $root "releases"
$repo = "https://github.com/tobitortosa/quemandan-launcher"

Write-Host "1. Compilando la aplicación" -ForegroundColor Cyan
# Autocontenida: el jugador no necesita instalar .NET. En carpeta y no en un solo
# archivo, porque los ejecutables autoextraíbles despiertan a los antivirus.
dotnet publish $project -c Release -r win-x64 --self-contained true `
  -p:PublishSingleFile=false -p:DebugType=none -p:DebugSymbols=false `
  -o $publishDir
if ($LASTEXITCODE -ne 0) { throw "falló la compilación" }

# Avalonia arrastra 100 MB de símbolos nativos que no sirven para nada.
Get-ChildItem $publishDir -Filter *.pdb -Recurse | Remove-Item -Force

$size = [math]::Round((Get-ChildItem $publishDir -Recurse | Measure-Object Length -Sum).Sum / 1MB, 1)
Write-Host "   carpeta lista: $size MB" -ForegroundColor DarkGray

Write-Host "2. Armando el instalador" -ForegroundColor Cyan
if (-not (Get-Command vpk -ErrorAction SilentlyContinue)) {
  dotnet tool install -g vpk
  $env:Path += ";$env:USERPROFILE\.dotnet\tools"
}

vpk pack --packId QueMandan --packVersion $Version --packDir $publishDir `
  --mainExe QueMandan.exe --packTitle "QUE MANDAN" --packAuthors "QUE MANDAN" `
  --channel $Channel --outputDir $releaseDir
if ($LASTEXITCODE -ne 0) { throw "falló el empaquetado" }

Get-ChildItem $releaseDir | ForEach-Object {
  "   {0}  {1} MB" -f $_.Name, [math]::Round($_.Length / 1MB, 1)
}

if ($Publish) {
  Write-Host "3. Publicando la versión $Version" -ForegroundColor Cyan
  vpk upload github --repoUrl $repo --publish --releaseName "QUE MANDAN $Version" `
    --tag "v$Version" --channel $Channel --outputDir $releaseDir
  if ($LASTEXITCODE -ne 0) { throw "falló la publicación" }
  Write-Host "   listo: $repo/releases" -ForegroundColor Green
} else {
  Write-Host "`nPara publicarla: pwsh ./pack-release.ps1 -Version $Version -Publish" -ForegroundColor DarkGray
}
