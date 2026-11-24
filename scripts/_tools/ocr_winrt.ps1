# OCR a list of images using Windows built-in OCR (Windows.Media.Ocr, WinRT).
# Usage: powershell -File ocr_winrt.ps1 -ImgPath "C:\path\to\img.jpg" [-TopN 40]
param(
    [Parameter(Mandatory=$true)][string]$ImgPath,
    [string]$OutFile = "",
    [double]$Scale = 2.0
)

$ErrorActionPreference = "Stop"

# Load WinRT types
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Ocr.OcrEngine, Windows.Media.Ocr, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.SoftwareBitmap, Windows.Graphics.Imaging, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Storage.Streams.RandomAccessStream, Windows.Storage.Streams, ContentType = WindowsRuntime]

$asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]

function Await($WinRtTask, $ResultType) {
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait()
    $netTask.Result
}

# List available OCR languages
$langs = [Windows.Media.Ocr.OcrEngine]::AvailableRecognizerLanguages
$langList = ($langs | ForEach-Object { "$($_.LanguageTag) $($_.DisplayName)" }) -join " | "

# Prefer zh-CN
$tag = $null
foreach ($l in $langs) { if ($l.LanguageTag -like "zh*") { $tag = $l; break } }
if (-not $tag) { $tag = $langs | Select-Object -First 1 }
Write-Host ("OCR langs available: " + $langList)
Write-Host ("Using: " + $tag.LanguageTag)

$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($tag)
if (-not $engine) { throw "Failed to create OCR engine for $($tag.LanguageTag)" }

# Open file
$fileAsync = [Windows.Storage.StorageFile]::GetFileFromPathAsync($ImgPath)
$file = Await $fileAsync ([Windows.Storage.StorageFile])

$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])

# Decode with optional scaling for better OCR on small text
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])

# Decode at native resolution (4-arg overload not projected in PS 5.1)
$softBmp = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])

$result = Await ($engine.RecognizeAsync($softBmp)) ([Windows.Media.Ocr.OcrResult])

$text = $result.Text
$lines = @()
foreach ($line in $result.Lines) { $lines += $line.Text }

$out = "=== OCR RESULT for $ImgPath ===`r`n$langs line count: $($result.Lines.Count)`r`n--- FULL TEXT ---`r`n$text`r`n"
if ($OutFile -ne "") {
    $out | Out-File -FilePath $OutFile -Encoding utf8
    Write-Host ("Written to " + $OutFile)
} else {
    Write-Output $out
}
