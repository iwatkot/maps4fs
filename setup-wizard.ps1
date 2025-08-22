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

function Wait-ForUserInput {
    param(
        [string]$PromptText = "Waiting for input"
    )
    
    Write-Host ""
    Write-Host "$PromptText " -ForegroundColor Yellow -NoNewline
    
    $dots = @(".", "..", "...", "")
    $counter = 0
    
    do {
        Write-Host "`r$PromptText $($dots[$counter % 4])" -ForegroundColor Yellow -NoNewline
        $counter++
        
        if ([Console]::KeyAvailable) {
            $key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Write-Host ""  # New line after input
            return $key
        }
        
        Start-Sleep -Milliseconds 500
    } while ($true)
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
        $key = Wait-ForUserInput -PromptText ">> Waiting for your choice (Y/N)"
        $choice = $key.Character.ToString().ToUpper()
        
        if ($choice -eq "Y") {
            return $true
        } elseif ($choice -eq "N") {
            return $false
        } else {
            Write-Host "Please press Y or N" -ForegroundColor Red
            Start-Sleep -Seconds 1
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
        $key = Wait-ForUserInput -PromptText ">> Ready to check Docker (Y/N)"
        $choice = $key.Character.ToString().ToUpper()
        
        if ($choice -eq "Y") {
            return $true
        } elseif ($choice -eq "N") {
            return $false
        } else {
            Write-Host "Please press Y or N" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    } while ($true)
}

function Test-DockerInstalled {
    # DEBUG: Force failure for testing
    return @{
        Installed = $false
        Version = $null
        Message = "Docker command not found (DEBUG MODE)"
    }
    
    # Original code (commented out for debug)
    <#
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
    #>
}

function Download-DockerDesktop {
    try {
        $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        $outputPath = "$env:TEMP\DockerDesktopInstaller.exe"
        
        Write-Host ""
        Write-Host "Downloading Docker Desktop installer..." -ForegroundColor Yellow
        Write-Host "This may take a few minutes depending on your connection" -ForegroundColor Gray
        Write-Host ""
        
        # Show progress
        $progressParams = @{
            Activity = "Downloading Docker Desktop"
            Status = "Please wait..."
            PercentComplete = 0
        }
        Write-Progress @progressParams
        
        # Download with progress
        Invoke-WebRequest -Uri $dockerUrl -OutFile $outputPath -UseBasicParsing
        
        Write-Progress @progressParams -Completed
        Write-Host "Download completed!" -ForegroundColor Green
        Write-Host "Installer saved to: $outputPath" -ForegroundColor Gray
        
        return @{
            Success = $true
            FilePath = $outputPath
            Message = "Docker Desktop installer downloaded successfully"
        }
        
    } catch {
        Write-Host "Failed to download Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
        return @{
            Success = $false
            FilePath = $null
            Message = "Download failed: $($_.Exception.Message)"
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
        $titleColor = "Green"
    } else {
        $statusContent = @(
            "",
            "                            [X] DOCKER NOT FOUND",
            "",
            "                    Docker is not installed or not accessible",
            "",
            "                           You have two options:",
            "",
            "                 1. Download manually from Docker website:",
            "                   https://www.docker.com/products/docker-desktop",
            "",
            "                 2. Press Y to download the installer here",
            "",
            "---",
            "",
            "                    Press Y to download or N to exit",
            ""
        )
        $title = "DOCKER CHECK - FAILED"
        $titleColor = "Red"
    }
    
    # Show frame with colored title
    Clear-Host
    
    # Top border
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    # Title with appropriate color
    $padding = (80 - $title.Length - 2) / 2
    $leftPadding = [int][Math]::Floor($padding)
    $rightPadding = [int][Math]::Ceiling($padding)
    Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor $titleColor
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    # Content with colored status line
    foreach ($line in $statusContent) {
        if ($line -eq "---") {
            Write-Host ("-" * 80) -ForegroundColor Gray
        } elseif ($line.Contains("[OK] DOCKER FOUND")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
        } elseif ($line.Contains("[X] DOCKER NOT FOUND")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Red
        } elseif ($line.Contains("1. Download manually") -or $line.Contains("2. Press Y to download")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Yellow
        } else {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
        }
    }
    
    # Bottom border
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    if ($DockerResult.Installed) {
        do {
            $key = Wait-ForUserInput -PromptText ">> Continue with setup (Y/N)"
            $choice = $key.Character.ToString().ToUpper()
            
            if ($choice -eq "Y") {
                return $true
            } elseif ($choice -eq "N") {
                return $false
            } else {
                Write-Host "Please press Y or N" -ForegroundColor Red
                Start-Sleep -Seconds 1
            }
        } while ($true)
    } else {
        do {
            $key = Wait-ForUserInput -PromptText ">> Download Docker Desktop (Y/N)"
            $choice = $key.Character.ToString().ToUpper()
            
            if ($choice -eq "Y") {
                # Download Docker Desktop
                $downloadResult = Download-DockerDesktop
                
                if ($downloadResult.Success) {
                    $downloadContent = @(
                        "",
                        "                        [OK] DOWNLOAD COMPLETED",
                        "",
                        "                Docker Desktop installer has been downloaded",
                        "",
                        "                     File location: $($downloadResult.FilePath)",
                        "",
                        "                   Please run the installer and restart this",
                        "                          wizard after installation",
                        "",
                        "---",
                        "",
                        "                       Press any key to exit",
                        ""
                    )
                    Show-Frame -Content $downloadContent -Title "DOWNLOAD SUCCESS"
                    $key = Wait-ForUserInput -PromptText ">> Press any key to exit"
                } else {
                    $errorContent = @(
                        "",
                        "                        [X] DOWNLOAD FAILED",
                        "",
                        "                     Failed to download installer",
                        "",
                        "                  Please download manually from:",
                        "                https://www.docker.com/products/docker-desktop",
                        "",
                        "---",
                        "",
                        "                       Press any key to exit",
                        ""
                    )
                    Show-Frame -Content $errorContent -Title "DOWNLOAD ERROR"
                    $key = Wait-ForUserInput -PromptText ">> Press any key to exit"
                }
                return $false
            } elseif ($choice -eq "N") {
                return $false
            } else {
                Write-Host "Please press Y or N" -ForegroundColor Red
                Start-Sleep -Seconds 1
            }
        } while ($true)
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
