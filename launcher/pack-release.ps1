# Arma el instalador del launcher y lo publica como release del repositorio.
#
#   pwsh ./pack-release.ps1 -Version 1.0.0
#
# Deja en releases/ un Setup.exe para el que instala por primera vez, y los archivos
# que el launcher ya instalado usa para actualizarse solo.
#
# OJO: no se puede correr primero sin -Publish para ver que salga bien y despues
# con -Publish. La segunda corrida se cae con "There is a release in channel win
# which is equal or greater to the current version", porque vpk mira releases/ y
# encuentra los .nupkg que dejo la primera. Si pasa, borrar los de esa version:
#   Remove-Item releases/SobrinosDePepe-<version>-*.nupkg
# y volver a correr. Lo mas simple es correrlo una sola vez con -Publish.

param(
  [Parameter(Mandatory = $true)][string]$Version,
  [string]$Channel = "win",
  [switch]$Publish,
  [string]$Token = $env:GITHUB_TOKEN
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$project = Join-Path $root "src/SobrinosDePepe.App/SobrinosDePepe.App.csproj"
$publishDir = Join-Path $root "artifacts/publish"
$releaseDir = Join-Path $root "releases"
$repo = "https://github.com/tobitortosa/sobrinosdepepe-launcher"
$icon = Join-Path $root "../brand/icon.ico"
$splash = Join-Path $root "../brand/logo-256.png"

Write-Host "1. Compilando la aplicación" -ForegroundColor Cyan
# Autocontenida: el jugador no necesita instalar .NET. En carpeta y no en un solo
# archivo, porque los ejecutables autoextraíbles despiertan a los antivirus.
# La versión va compilada adentro: el launcher la muestra abajo de todo.
dotnet publish $project -c Release -r win-x64 --self-contained true `
  -p:Version=$Version `
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

# El ícono va también en el instalador, que es el archivo que la gente descarga,
# y la imagen se muestra mientras instala.
vpk pack --packId SobrinosDePepe --packVersion $Version --packDir $publishDir `
  --mainExe SobrinosDePepe.exe --packTitle "SOBRINOS DE PEPE" --packAuthors "SOBRINOS DE PEPE" `
  --icon $icon --splashImage $splash --splashProgressColor "#4ADE80" `
  --channel $Channel --outputDir $releaseDir
if ($LASTEXITCODE -ne 0) { throw "falló el empaquetado" }

Get-ChildItem $releaseDir | ForEach-Object {
  "   {0}  {1} MB" -f $_.Name, [math]::Round($_.Length / 1MB, 1)
}

if ($Publish) {
  Write-Host "3. Publicando la versión $Version" -ForegroundColor Cyan
  if (-not $Token) { $Token = (& gh auth token).Trim() }
  if (-not $Token) { throw "falta el token de GitHub: pasá -Token o iniciá sesión con gh auth login" }

  vpk upload github --repoUrl $repo --token $Token --publish `
    --releaseName "SOBRINOS DE PEPE $Version" --tag "v$Version" `
    --channel $Channel --outputDir $releaseDir
  if ($LASTEXITCODE -ne 0) { throw "falló la publicación" }
  Write-Host "   listo: $repo/releases" -ForegroundColor Green
} else {
  Write-Host "`nPara publicarla: pwsh ./pack-release.ps1 -Version $Version -Publish" -ForegroundColor DarkGray
}
