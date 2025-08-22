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
        "         No paid features exist, if someone asks for payment it's a scam",
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

function Show-DockerRequirement {
    $dockerContent = @(
        "",
        "                           DOCKER REQUIREMENT",
        "",
        "                 The local version requires Docker to be installed",
        "",
        "                        Docker will be used to run Maps4FS",
        "                          in a containerized environment",
        "",
        "---",
        "",
        "                    The wizard will now check if Docker is",
        "                           installed on your system",
        "",
        "---",
        "",
        "                    Press Y to proceed or N to cancel",
        ""
    )
    
    Show-Frame -Content $dockerContent -Title "DOCKER INSTALLATION CHECK"
    
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

function Test-DockerInstalled {
    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            return @{
                Installed = $true
                Version = $dockerVersion
                Message = "Docker is installed and accessible"
            }
        } else {
            return @{
                Installed = $false
                Version = $null
                Message = "Docker command not found"
            }
        }
    } catch {
        return @{
            Installed = $false
            Version = $null
            Message = "Error checking Docker: $($_.Exception.Message)"
        }
    }
}

function Show-DockerStatus {
    param([hashtable]$DockerResult)
    
    if ($DockerResult.Installed) {
        $statusContent = @(
            "",
            "                            [OK] DOCKER FOUND",
            "",
            "                     Docker is installed and ready to use",
            "",
            "                 Version: $($DockerResult.Version)",
            "",
            "---",
            "",
            "                     Press Y to continue with setup",
            "                       or N to exit the wizard",
            ""
        )
        $title = "DOCKER CHECK - SUCCESS"
        $color = "Green"
    } else {
        $statusContent = @(
            "",
            "                            [X] DOCKER NOT FOUND",
            "",
            "                    Docker is not installed or not accessible",
            "",
            "                    Please install Docker Desktop from:",
            "                      https://www.docker.com/products/docker-desktop",
            "",
            "                        After installation, restart this wizard",
            "",
            "---",
            "",
            "                         Press any key to exit",
            ""
        )
        $title = "DOCKER CHECK - FAILED"
        $color = "Red"
    }
    
    Show-Frame -Content $statusContent -Title $title
    
    if ($DockerResult.Installed) {
        do {
            $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            $choice = $key.Character.ToString().ToUpper()
            
            if ($choice -eq "Y") {
                return $true
            } elseif ($choice -eq "N") {
                return $false
            }
        } while ($true)
    } else {
        $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null
        return $false
    }
}

# Main execution
try {
    # Step 1: Welcome screen
    $continue = Show-Welcome
    
    if (-not $continue) {
        Show-Frame -Content @("", "                           Setup cancelled by user", "") -Title "GOODBYE"
        Start-Sleep -Seconds 2
        exit 0
    }
    
    # Step 2: Docker requirement information
    $dockerProceed = Show-DockerRequirement
    
    if (-not $dockerProceed) {
        Show-Frame -Content @("", "                           Setup cancelled by user", "") -Title "GOODBYE"
        Start-Sleep -Seconds 2
        exit 0
    }
    
    # Step 3: Check if Docker is installed
    Write-Host "Checking Docker installation..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
    
    $dockerResult = Test-DockerInstalled
    $dockerContinue = Show-DockerStatus -DockerResult $dockerResult
    
    if (-not $dockerContinue) {
        Show-Frame -Content @("", "                              Setup aborted", "") -Title "GOODBYE"
        Start-Sleep -Seconds 2
        exit 0
    }
    
    # Step 4: Continue with next steps...
    Show-Frame -Content @("", "                     Docker check passed successfully!", "", "                        ... (More steps to implement)", "") -Title "SETUP IN PROGRESS"
    
    # Placeholder for next steps
    Write-Host ""
    Write-Host "Next steps would be implemented here..." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    
} catch {
    Write-Host "An error occurred: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
