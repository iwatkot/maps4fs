# Maps4FS Setup Wizard
# Author: https://github.com/iwatkot
# Repository: https://github.com/iwatkot/maps4fs

function Show-Frame {
    param(
        [string[]]$Content,
        [string]$Title = ""
    )
    
    Clear-Host
    
    # Top border
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    if ($Title) {
        $padding = (80 - $Title.Length - 2) / 2
        $leftPadding = [int][Math]::Floor($padding)
        $rightPadding = [int][Math]::Ceiling($padding)
        Write-Host (("=" * $leftPadding) + " " + $Title + " " + ("=" * $rightPadding)) -ForegroundColor Cyan
        Write-Host ("=" * 80) -ForegroundColor Cyan
    }
    
    # Content with side borders
    foreach ($line in $Content) {
        if ($line -eq "---") {
            Write-Host ("-" * 80) -ForegroundColor Gray
        } else {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
        }
    }
    
    # Bottom border
    Write-Host ("=" * 80) -ForegroundColor Cyan
}

function Show-Welcome {
    $welcomeContent = @(
        "",
        "                    Maps4FS Local Version Deployment",
        "",
        "                    Public app: https://maps4fs.xyz/",
        "                    Author: https://github.com/iwatkot",
        "                    Repo: https://github.com/iwatkot/maps4fs",
        "",
        "---",
        "",
        "              Maps4FS is completely free and open source tool",
        "",
        "         No paid features exis, if someone asks for payment it's a scam",
        "                        Use only official sources",
        "",
        "---",
        "",
        "                      Press Y to continue or N to exit",
        ""
    )
    
    Show-Frame -Content $welcomeContent -Title "WELCOME TO MAPS4FS SETUP WIZARD"
    
    do {
        $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        $choice = $key.Character.ToString().ToUpper()
        
        if ($choice -eq "Y") {
            return $true
        } elseif ($choice -eq "N") {
            return $false
        }
    } while ($true)
}

# Main execution
try {
    $continue = Show-Welcome
    
    if (-not $continue) {
        Show-Frame -Content @("", "                           Setup cancelled by user", "") -Title "GOODBYE"
        Start-Sleep -Seconds 2
        exit 0
    }
    
    # Continue with next steps...
    Show-Frame -Content @("", "                           Setup will continue...", "", "                        (More steps to be implemented)", "") -Title "SETUP IN PROGRESS"
    
    # Placeholder for next steps
    Write-Host ""
    Write-Host "Next steps would be implemented here..." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    
} catch {
    Write-Host "An error occurred: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
