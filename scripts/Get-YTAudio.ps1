param(
	[Parameter(Mandatory=$true)]
	[string]$Code,

	[Parameter(Mandatory=$true)]
	[ValidateSet("ogg","wav")]
	[string]$Format
)

# Build URL from code
$url = "https://www.youtube.com/watch?v=$Code"

# Temporary download filename
$temp = "$Code.mp3"

Write-Host "Downloading video audio..."
yt-dlp -f "ba" --extract-audio --audio-format mp3 -o "$Code.%(ext)s" $url

if (-not (Test-Path $temp)) {
	Write-Host "Download failed."
	return
}

# Output filename
$output = "$Code.$Format"

Write-Host "Converting to $Format..."
switch ($Format) {
	"ogg" { ffmpeg -i $temp -c:a libvorbis $output -y }
	"wav" { ffmpeg -i $temp -c:a pcm_s16le $output -y }
}

Write-Host "Cleaning up..."
Remove-Item $temp

Write-Host "Done! Saved as $output"
