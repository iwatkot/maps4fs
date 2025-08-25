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

function Test-DockerRunning {
    param(
        [bool]$ShowTestMessage = $true
    )
    
    try {
        if ($ShowTestMessage) {
            Write-Host ">> Testing Docker with hello-world container..." -ForegroundColor Yellow
        }
        
        # Run hello-world container and capture output
        $dockerOutput = docker run --rm hello-world 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            if ($ShowTestMessage) {
                Write-Host ">> Docker is running correctly!" -ForegroundColor Green
            }
            
            # Clean up any leftover hello-world images
            docker rmi hello-world 2>$null | Out-Null
            
            return @{
                Running = $true
                Output = $dockerOutput
                Message = "Docker is running and accessible"
            }
        } else {
            return @{
                Running = $false
                Output = $dockerOutput
                Message = "Docker is not running or not accessible"
            }
        }
    } catch {
        return @{
            Running = $false
            Output = $null
            Message = "Error testing Docker: $($_.Exception.Message)"
        }
    }
}

function Show-DockerRunningStatus {
    param([hashtable]$DockerRunResult)
    
    if ($DockerRunResult.Running) {
        $statusContent = @(
            "",
            "                            [OK] DOCKER IS RUNNING",
            "",
            "                     Docker is installed and running correctly!",
            "",
            "                        Hello-world test completed successfully",
            "",
            "---",
            "",
            "                     Press Y to continue with setup",
            "                       or N to exit the wizard",
            ""
        )
        $titleColor = "Green"
    } else {
        $statusContent = @(
            "",
            "                            [X] DOCKER NOT RUNNING",
            "",
            "                    Docker is installed but not running properly",
            "",
            "                           We can try to fix this:",
            "",
            "                     Y - Launch Docker Desktop automatically",
            "                     N - Exit (launch manually later)",
            "",
            "---",
            "",
            "                    Press Y to launch or N to exit",
            ""
        )
        $titleColor = "Red"
    }
    
    $title = if ($DockerRunResult.Running) { "DOCKER TEST - SUCCESS" } else { "DOCKER TEST - FAILED" }
    
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
        } elseif ($line.Contains("[OK] DOCKER IS RUNNING")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
        } elseif ($line.Contains("[X] DOCKER NOT RUNNING")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Red
        } elseif ($line.Contains("Y - Launch Docker") -or $line.Contains("N - Exit")) {
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
    
    if ($DockerRunResult.Running) {
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
            $key = Wait-ForUserInput -PromptText ">> Launch Docker Desktop (Y/N)"
            $choice = $key.Character.ToString().ToUpper()
            
            if ($choice -eq "Y") {
                # Try to launch Docker Desktop
                Write-Host ""
                Write-Host "Launching Docker Desktop..." -ForegroundColor Yellow
                
                try {
                    # Try docker command first (newer versions support this)
                    Write-Host ">> Trying docker command..." -ForegroundColor Gray
                    
                    $dockerStartResult = docker desktop start 2>$null
                    if ($LASTEXITCODE -eq 0) {
                        Write-Host ">> Docker Desktop launched successfully!" -ForegroundColor Green
                        
                        $launchContent = @(
                            "",
                            "                         DOCKER DESKTOP STARTED",
                            "",
                            "                    Docker Desktop is starting up...",
                            "",
                            "                           Please wait for:",
                            "                    1. Docker Desktop to fully start",
                            "                    2. Docker engine to become ready",
                            "                    3. System tray icon to show 'running'",
                            "",
                            "                      This may take a few minutes",
                            "",
                            "                    Press Y when ready to test Docker",
                            "                         or N to exit",
                            "",
                            "---",
                            "",
                            "                    Press Y to test or N to exit",
                            ""
                        )
                        Show-Frame -Content $launchContent -Title "DOCKER DESKTOP STARTING"
                        
                        do {
                            $key = Wait-ForUserInput -PromptText ">> Test Docker now (Y/N)"
                            $choice = $key.Character.ToString().ToUpper()
                            
                            if ($choice -eq "Y") {
                                # Re-test Docker after startup
                                Write-Host ""
                                Write-Host "Re-testing Docker functionality..." -ForegroundColor Yellow
                                Start-Sleep -Seconds 2
                                
                                $retestResult = Test-DockerRunning -ShowTestMessage $false
                                if ($retestResult.Running) {
                                    # Success! Docker is now running
                                    $successContent = @(
                                        "",
                                        "                        [OK] DOCKER IS NOW RUNNING",
                                        "",
                                        "                   Docker Desktop started successfully!",
                                        "",
                                        "                    Hello-world test completed successfully",
                                        "",
                                        "---",
                                        "",
                                        "                     Press Y to continue with setup",
                                        "                       or N to exit the wizard",
                                        ""
                                    )
                                    
                                    Clear-Host
                                    Write-Host ("=" * 80) -ForegroundColor Cyan
                                    $title = "DOCKER TEST - SUCCESS"
                                    $padding = (80 - $title.Length - 2) / 2
                                    $leftPadding = [int][Math]::Floor($padding)
                                    $rightPadding = [int][Math]::Ceiling($padding)
                                    Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Green
                                    Write-Host ("=" * 80) -ForegroundColor Cyan
                                    
                                    foreach ($line in $successContent) {
                                        if ($line -eq "---") {
                                            Write-Host ("-" * 80) -ForegroundColor Gray
                                        } elseif ($line.Contains("[OK] DOCKER IS NOW RUNNING")) {
                                            $contentLength = $line.Length
                                            $padding = 80 - $contentLength - 2
                                            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
                                        } else {
                                            $contentLength = $line.Length
                                            $padding = 80 - $contentLength - 2
                                            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
                                        }
                                    }
                                    Write-Host ("=" * 80) -ForegroundColor Cyan
                                    
                                    do {
                                        $finalKey = Wait-ForUserInput -PromptText ">> Continue with setup (Y/N)"
                                        $finalChoice = $finalKey.Character.ToString().ToUpper()
                                        
                                        if ($finalChoice -eq "Y") {
                                            return $true  # Continue with setup
                                        } elseif ($finalChoice -eq "N") {
                                            return $false
                                        } else {
                                            Write-Host "Please press Y or N" -ForegroundColor Red
                                            Start-Sleep -Seconds 1
                                        }
                                    } while ($true)
                                    
                                } else {
                                    # Still not working
                                    Write-Host "Docker is still not responding properly" -ForegroundColor Red
                                    Write-Host "Docker Desktop may need more time to start" -ForegroundColor Yellow
                                    Write-Host "Please wait a bit longer and try again" -ForegroundColor Yellow
                                    Start-Sleep -Seconds 3
                                    # Return to the waiting screen
                                    Show-Frame -Content $launchContent -Title "DOCKER DESKTOP STARTING"
                                }
                                
                            } elseif ($choice -eq "N") {
                                return $false
                            } else {
                                Write-Host "Please press Y or N" -ForegroundColor Red
                                Start-Sleep -Seconds 1
                            }
                        } while ($true)
                        return $false
                    } else {
                        # Docker command failed - installation issue
                        Write-Host ">> Docker command failed" -ForegroundColor Red
                        
                        $errorContent = @(
                            "",
                            "                        [X] CANNOT LAUNCH DOCKER",
                            "",
                            "                    Docker installation appears incomplete",
                            "",
                            "                           This usually means:",
                            "                    1. Docker Desktop needs to be reinstalled",
                            "                    2. Docker is not in system PATH",
                            "                    3. Installation was corrupted",
                            "",
                            "                    Please check your Docker installation",
                            "                      and try launching from Start Menu",
                            "",
                            "---",
                            "",
                            "                       Press any key to exit",
                            ""
                        )
                        Show-Frame -Content $errorContent -Title "INSTALLATION PROBLEM"
                        $key = Wait-ForUserInput -PromptText ">> Press any key to exit"
                        return $false
                    }
                    
                } catch {
                    Write-Host "Failed to launch Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
                    Start-Sleep -Seconds 3
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

function Download-DockerDesktop {
    try {
        $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
        $outputPath = ".\DockerDesktopInstaller.exe"
        $fullPath = (Resolve-Path ".").Path + "\DockerDesktopInstaller.exe"
        
        # Show clean download screen
        $downloadContent = @(
            "",
            "                        DOWNLOADING DOCKER DESKTOP",
            "",
            "                      Please wait while we download the",
            "                         Docker Desktop installer...",
            "",
            "                    File will be saved to current directory:",
            "                           $((Get-Location).Path)",
            "",
            "                              Please be patient!",
            ""
        )
        Show-Frame -Content $downloadContent -Title "DOWNLOAD IN PROGRESS"
        
        Write-Host ""
        
        # Simple clean download without progress mess
        try {
            # Show animated dots while downloading
            $job = Start-Job -ScriptBlock {
                param($url, $path)
                $ProgressPreference = 'SilentlyContinue'  # Hide ugly progress
                Invoke-WebRequest -Uri $url -OutFile $path -UseBasicParsing
            } -ArgumentList $dockerUrl, $fullPath
            
            # Show simple animated progress
            $dots = @(".", "..", "...", "")
            $counter = 0
            
            while ($job.State -eq "Running") {
                Write-Host "`r>> Downloading Docker Desktop $($dots[$counter % 4])" -ForegroundColor Yellow -NoNewline
                $counter++
                Start-Sleep -Milliseconds 800
            }
            
            # Check if job completed successfully
            $jobResult = Receive-Job -Job $job
            Remove-Job -Job $job
            
            Write-Host ""
            Write-Host ""
            Write-Host "Download completed successfully!" -ForegroundColor Green
            
            # Verify file exists and get final size
            if (Test-Path $fullPath) {
                $fileSize = [math]::Round((Get-Item $fullPath).Length / 1MB, 1)
                Write-Host "File size: $fileSize MB" -ForegroundColor Gray
                
                return @{
                    Success = $true
                    FilePath = $fullPath
                    FileName = "DockerDesktopInstaller.exe"
                    FileSize = $fileSize
                    Message = "Docker Desktop installer downloaded successfully"
                }
            } else {
                throw "Downloaded file not found"
            }
            
        } catch {
            throw $_
        }
        
    } catch {
        Write-Host ""
        Write-Host "Failed to download Docker Desktop: $($_.Exception.Message)" -ForegroundColor Red
        return @{
            Success = $false
            FilePath = $null
            FileName = $null
            FileSize = 0
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
                        "                Docker Desktop installer has been downloaded!",
                        "",
                        "                     File: $($downloadResult.FileName)",
                        "                     Size: $($downloadResult.FileSize) MB",
                        "                     Location: Current directory",
                        "",
                        "                           What would you like to do?",
                        "",
                        "                     Y - Launch installer now",
                        "                     N - Exit (launch manually later)",
                        "",
                        "---",
                        "",
                        "                    Press Y to launch or N to exit",
                        ""
                    )
                    
                    # Custom frame with green success message
                    Clear-Host
                    Write-Host ("=" * 80) -ForegroundColor Cyan
                    $title = "DOWNLOAD SUCCESS"
                    $padding = (80 - $title.Length - 2) / 2
                    $leftPadding = [int][Math]::Floor($padding)
                    $rightPadding = [int][Math]::Ceiling($padding)
                    Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Green
                    Write-Host ("=" * 80) -ForegroundColor Cyan
                    
                    foreach ($line in $downloadContent) {
                        if ($line -eq "---") {
                            Write-Host ("-" * 80) -ForegroundColor Gray
                        } elseif ($line.Contains("[OK] DOWNLOAD COMPLETED")) {
                            $contentLength = $line.Length
                            $padding = 80 - $contentLength - 2
                            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
                        } elseif ($line.Contains("Y - Launch installer") -or $line.Contains("N - Exit")) {
                            $contentLength = $line.Length
                            $padding = 80 - $contentLength - 2
                            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Yellow
                        } else {
                            $contentLength = $line.Length
                            $padding = 80 - $contentLength - 2
                            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
                        }
                    }
                    Write-Host ("=" * 80) -ForegroundColor Cyan
                    
                    # Ask user if they want to launch installer
                    do {
                        $key = Wait-ForUserInput -PromptText ">> Launch installer now (Y/N)"
                        $choice = $key.Character.ToString().ToUpper()
                        
                        if ($choice -eq "Y") {
                            # Launch installer
                            Write-Host ""
                            Write-Host "Launching Docker Desktop installer..." -ForegroundColor Yellow
                            
                            try {
                                Start-Process -FilePath $downloadResult.FilePath -Wait
                                
                                # After installation completion
                                $completionContent = @(
                                    "",
                                    "                         INSTALLATION COMPLETED",
                                    "",
                                    "                   Docker Desktop installation finished!",
                                    "",
                                    "                           Important notes:",
                                    "",
                                    "                   1. Restart your computer if prompted",
                                    "                   2. Start Docker Desktop from Start Menu",
                                    "                   3. Wait for Docker to fully start",
                                    "                   4. Run this wizard again to continue setup",
                                    "",
                                    "---",
                                    "",
                                    "                       Press any key to exit",
                                    ""
                                )
                                Show-Frame -Content $completionContent -Title "INSTALLATION COMPLETE"
                                $key = Wait-ForUserInput -PromptText ">> Press any key to exit"
                                
                            } catch {
                                Write-Host "Failed to launch installer: $($_.Exception.Message)" -ForegroundColor Red
                                Start-Sleep -Seconds 2
                            }
                            break
                        } elseif ($choice -eq "N") {
                            break
                        } else {
                            Write-Host "Please press Y or N" -ForegroundColor Red
                            Start-Sleep -Seconds 1
                        }
                    } while ($true)
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

# Function to check for existing maps4fs containers
function Test-ExistingContainers {
    try {
        Write-Host ">> Checking for existing maps4fs containers..." -ForegroundColor Yellow
        
        # Get all containers (running and stopped) with maps4fs in the name
        $containers = docker ps -a --filter "name=maps4fs" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}\t{{.Image}}" 2>$null
        
        if ($LASTEXITCODE -eq 0 -and $containers) {
            # Parse container information (skip header line)
            $containerLines = $containers -split "`n" | Select-Object -Skip 1 | Where-Object { $_.Trim() -ne "" }
            
            if ($containerLines.Count -gt 0) {
                $containerInfo = @()
                foreach ($line in $containerLines) {
                    $parts = $line -split "`t"
                    if ($parts.Count -ge 4) {
                        $containerInfo += @{
                            ID = $parts[0].Trim()
                            Name = $parts[1].Trim()
                            Status = $parts[2].Trim()
                            Image = $parts[3].Trim()
                            IsRunning = $parts[2] -match "Up"
                        }
                    }
                }
                
                return @{
                    Found = $true
                    Containers = $containerInfo
                    Message = "Found $($containerInfo.Count) maps4fs container(s)"
                }
            }
        }
        
        return @{
            Found = $false
            Containers = @()
            Message = "No maps4fs containers found"
        }
    } catch {
        return @{
            Found = $false
            Containers = @()
            Message = "Error checking containers: $($_.Exception.Message)"
        }
    }
}

# Function to stop and remove maps4fs containers
function Remove-ExistingContainers {
    param(
        [array]$Containers
    )
    
    $success = $true
    $results = @()
    
    foreach ($container in $Containers) {
        try {
            Write-Host ">> Processing container: $($container.Name)" -ForegroundColor Yellow
            
            # Stop container if running
            if ($container.IsRunning) {
                Write-Host "   Stopping running container..." -ForegroundColor Yellow
                docker stop $container.ID 2>$null | Out-Null
                if ($LASTEXITCODE -ne 0) {
                    $results += "Failed to stop $($container.Name)"
                    $success = $false
                    continue
                }
            }
            
            # Remove container
            Write-Host "   Removing container..." -ForegroundColor Yellow
            docker rm $container.ID 2>$null | Out-Null
            if ($LASTEXITCODE -ne 0) {
                $results += "Failed to remove $($container.Name)"
                $success = $false
            } else {
                $results += "Successfully removed $($container.Name)"
            }
            
        } catch {
            $results += "Error processing $($container.Name): $($_.Exception.Message)"
            $success = $false
        }
    }
    
    return @{
        Success = $success
        Results = $results
    }
}

# Function to show existing containers and prompt for removal
function Show-ExistingContainers {
    param(
        [object]$ContainerResult
    )
    
    if (-not $ContainerResult.Found) {
        # No containers found - show brief success message
        $noContainersContent = @(
            "",
            "                        [OK] NO EXISTING CONTAINERS",
            "",
            "                      No maps4fs containers found",
            "",
            "                         Ready to proceed!",
            "",
            "---",
            "",
            "                      Press any key to continue",
            ""
        )
        
        Clear-Host
        Write-Host ("=" * 80) -ForegroundColor Cyan
        $title = "CONTAINER CHECK - CLEAN"
        $padding = (80 - $title.Length - 2) / 2
        $leftPadding = [int][Math]::Floor($padding)
        $rightPadding = [int][Math]::Ceiling($padding)
        Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Green
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        foreach ($line in $noContainersContent) {
            if ($line -eq "---") {
                Write-Host ("-" * 80) -ForegroundColor Gray
            } elseif ($line.Contains("[OK] NO EXISTING CONTAINERS")) {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
            } else {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
            }
        }
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        $key = Wait-ForUserInput -PromptText ">> Press any key to continue"
        return $true
    }
    
    # Show existing containers
    $containerContent = @(
        "",
        "                      [!] EXISTING CONTAINERS FOUND",
        "",
        "                     Found maps4fs containers that may",
        "                        conflict with new deployment:",
        ""
    )
    
    # Add container details
    foreach ($container in $ContainerResult.Containers) {
        $status = if ($container.IsRunning) { "RUNNING" } else { "STOPPED" }
        $statusColor = if ($container.IsRunning) { "Red" } else { "Yellow" }
        $containerContent += "                  * $($container.Name) [$status]"
    }
    
    $containerContent += @(
        "",
        "                      It's recommended to remove these",
        "                      containers before proceeding.",
        "",
        "---",
        "",
        "                 Y - Stop and remove all containers",
        "                 N - Continue without removing",
        "                 E - Exit wizard",
        ""
    )
    
    Clear-Host
    Write-Host ("=" * 80) -ForegroundColor Cyan
    $title = "EXISTING CONTAINERS DETECTED"
    $padding = (80 - $title.Length - 2) / 2
    $leftPadding = [int][Math]::Floor($padding)
    $rightPadding = [int][Math]::Ceiling($padding)
    Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Yellow
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    foreach ($line in $containerContent) {
        if ($line -eq "---") {
            Write-Host ("-" * 80) -ForegroundColor Gray
        } elseif ($line.Contains("[!] EXISTING CONTAINERS FOUND")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Yellow
        } elseif ($line.Contains("RUNNING")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Red
        } elseif ($line.Contains("STOPPED")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Yellow
        } else {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
        }
    }
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    # Wait for user choice
    do {
        $key = Wait-ForUserInput -PromptText ">> Remove containers (Y/N/E)"
        $choice = $key.Character.ToString().ToUpper()
        
        if ($choice -eq "Y") {
            # Remove containers
            Write-Host ""
            Write-Host "Removing existing containers..." -ForegroundColor Yellow
            
            $removeResult = Remove-ExistingContainers -Containers $ContainerResult.Containers
            
            # Show removal results
            $resultContent = @("", "                          CONTAINER REMOVAL RESULTS", "")
            
            foreach ($result in $removeResult.Results) {
                $resultContent += "                  $result"
            }
            
            if ($removeResult.Success) {
                $resultContent += @(
                    "",
                    "                    [OK] All containers removed successfully",
                    "",
                    "---",
                    "",
                    "                      Press any key to continue",
                    ""
                )
                $titleColor = "Green"
                $titleText = "CONTAINERS REMOVED"
            } else {
                $resultContent += @(
                    "",
                    "                   [!] Some containers failed to remove",
                    "",
                    "                     You may need to remove them manually",
                    "",
                    "---",
                    "",
                    "                 Y - Continue anyway",
                    "                 N - Exit wizard",
                    ""
                )
                $titleColor = "Yellow"
                $titleText = "PARTIAL SUCCESS"
            }
            
            Clear-Host
            Write-Host ("=" * 80) -ForegroundColor Cyan
            $title = $titleText
            $padding = (80 - $title.Length - 2) / 2
            $leftPadding = [int][Math]::Floor($padding)
            $rightPadding = [int][Math]::Ceiling($padding)
            Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor $titleColor
            Write-Host ("=" * 80) -ForegroundColor Cyan
            
            foreach ($line in $resultContent) {
                if ($line -eq "---") {
                    Write-Host ("-" * 80) -ForegroundColor Gray
                } elseif ($line.Contains("[OK]")) {
                    $contentLength = $line.Length
                    $padding = 80 - $contentLength - 2
                    Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
                } elseif ($line.Contains("[!]")) {
                    $contentLength = $line.Length
                    $padding = 80 - $contentLength - 2
                    Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Yellow
                } else {
                    $contentLength = $line.Length
                    $padding = 80 - $contentLength - 2
                    Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
                }
            }
            Write-Host ("=" * 80) -ForegroundColor Cyan
            
            if ($removeResult.Success) {
                $key = Wait-ForUserInput -PromptText ">> Press any key to continue"
                return $true
            } else {
                # Partial success - ask if continue
                do {
                    $continueKey = Wait-ForUserInput -PromptText ">> Continue anyway (Y/N)"
                    $continueChoice = $continueKey.Character.ToString().ToUpper()
                    
                    if ($continueChoice -eq "Y") {
                        return $true
                    } elseif ($continueChoice -eq "N") {
                        return $false
                    } else {
                        Write-Host "Please press Y or N" -ForegroundColor Red
                        Start-Sleep -Seconds 1
                    }
                } while ($true)
            }
            
        } elseif ($choice -eq "N") {
            return $true  # Continue without removing
        } elseif ($choice -eq "E") {
            return $false  # Exit
        } else {
            Write-Host "Please press Y, N, or E" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    } while ($true)
}

# Function to check if a port is available
function Test-PortAvailable {
    param(
        [int]$Port
    )
    
    try {
        $tcpListener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Any, $Port)
        $tcpListener.Start()
        $tcpListener.Stop()
        
        return @{
            Available = $true
            Port = $Port
            Message = "Port $Port is available"
        }
    } catch {
        return @{
            Available = $false
            Port = $Port
            Message = "Port $Port is in use"
            Error = $_.Exception.Message
        }
    }
}

# Function to check required ports for maps4fs
function Test-RequiredPorts {
    $requiredPorts = @(3000, 8000)
    $results = @()
    
    Write-Host ">> Checking required ports..." -ForegroundColor Yellow
    
    foreach ($port in $requiredPorts) {
        Write-Host "   Checking port $port..." -ForegroundColor Gray
        $portResult = Test-PortAvailable -Port $port
        $results += $portResult
        
        if ($portResult.Available) {
            Write-Host "   Port $port is available" -ForegroundColor Green
        } else {
            Write-Host "   Port $port is in use" -ForegroundColor Red
        }
    }
    
    $allAvailable = ($results | Where-Object { -not $_.Available }).Count -eq 0
    
    return @{
        AllAvailable = $allAvailable
        Results = $results
        Message = if ($allAvailable) { "All required ports are available" } else { "Some required ports are in use" }
    }
}

# Function to show port availability results
function Show-PortAvailability {
    param(
        [object]$PortResult
    )
    
    if ($PortResult.AllAvailable) {
        # All ports available - show success
        $successContent = @(
            "",
            "                        [OK] PORTS AVAILABLE",
            "",
            "                     All required ports are free:",
            "",
            "                          * Port 3000: Available",
            "                          * Port 8000: Available", 
            "",
            "                         Ready to proceed!",
            "",
            "---",
            "",
            "                      Press any key to continue",
            ""
        )
        
        Clear-Host
        Write-Host ("=" * 80) -ForegroundColor Cyan
        $title = "PORT CHECK - SUCCESS"
        $padding = (80 - $title.Length - 2) / 2
        $leftPadding = [int][Math]::Floor($padding)
        $rightPadding = [int][Math]::Ceiling($padding)
        Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Green
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        foreach ($line in $successContent) {
            if ($line -eq "---") {
                Write-Host ("-" * 80) -ForegroundColor Gray
            } elseif ($line.Contains("[OK] PORTS AVAILABLE")) {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
            } else {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
            }
        }
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        $key = Wait-ForUserInput -PromptText ">> Press any key to continue"
        return $true
    }
    
    # Some ports are in use - show error
    $errorContent = @(
        "",
        "                        [!] PORTS REQUIRED",
        "",
        "                    Maps4fs requires these ports:",
        ""
    )
    
    # Add port status details
    foreach ($result in $PortResult.Results) {
        if ($result.Available) {
            $errorContent += "                        * Port $($result.Port): Available"
        } else {
            $errorContent += "                        * Port $($result.Port): IN USE"
        }
    }
    
    $errorContent += @(
        "",
        "                    Please free the required ports:",
        "",
        "                   - Port 3000: Frontend application",
        "                   - Port 8000: Backend API server",
        "",
        "                    Close applications using these ports",
        "                       and run the wizard again.",
        "",
        "---",
        "",
        "                      Press any key to exit",
        ""
    )
    
    Clear-Host
    Write-Host ("=" * 80) -ForegroundColor Cyan
    $title = "PORT CHECK - FAILED"
    $padding = (80 - $title.Length - 2) / 2
    $leftPadding = [int][Math]::Floor($padding)
    $rightPadding = [int][Math]::Ceiling($padding)
    Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Red
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    foreach ($line in $errorContent) {
        if ($line -eq "---") {
            Write-Host ("-" * 80) -ForegroundColor Gray
        } elseif ($line.Contains("[!] PORTS REQUIRED")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Red
        } elseif ($line.Contains("IN USE")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Red
        } elseif ($line.Contains("Available")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
        } else {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
        }
    }
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    $key = Wait-ForUserInput -PromptText ">> Press any key to exit"
    return $false
}

# Function to check and create required directories
function Test-RequiredDirectories {
    $userProfile = $env:USERPROFILE
    $requiredDirectories = @(
        @{
            Path = "$userProfile\maps4fs\mfsrootdir"
            Description = "Maps working directory (shared storage for maps and cache)"
        },
        @{
            Path = "$userProfile\maps4fs\templates"
            Description = "Game templates directory (FS22/FS25 map templates)"
        }
    )
    
    $results = @()
    
    Write-Host ">> Checking required directories..." -ForegroundColor Yellow
    
    foreach ($dir in $requiredDirectories) {
        Write-Host "   Checking: $($dir.Path)" -ForegroundColor Gray
        
        if (Test-Path $dir.Path) {
            Write-Host "   Directory exists" -ForegroundColor Green
            $results += @{
                Path = $dir.Path
                Description = $dir.Description
                Exists = $true
                Created = $false
            }
        } else {
            Write-Host "   Directory does not exist" -ForegroundColor Red
            $results += @{
                Path = $dir.Path
                Description = $dir.Description
                Exists = $false
                Created = $false
            }
        }
    }
    
    $allExist = ($results | Where-Object { -not $_.Exists }).Count -eq 0
    
    return @{
        AllExist = $allExist
        Directories = $results
        Message = if ($allExist) { "All required directories exist" } else { "Some directories are missing" }
    }
}

# Function to create missing directories
function New-RequiredDirectories {
    param(
        [array]$MissingDirectories
    )
    
    $success = $true
    $createdDirs = @()
    
    foreach ($dir in $MissingDirectories) {
        try {
            Write-Host ">> Creating directory: $($dir.Path)" -ForegroundColor Yellow
            New-Item -ItemType Directory -Path $dir.Path -Force | Out-Null
            
            if (Test-Path $dir.Path) {
                Write-Host "   Successfully created" -ForegroundColor Green
                $dir.Created = $true
                $createdDirs += $dir.Path
            } else {
                throw "Directory creation failed"
            }
        } catch {
            Write-Host "   Failed to create directory: $($_.Exception.Message)" -ForegroundColor Red
            $success = $false
        }
    }
    
    return @{
        Success = $success
        CreatedDirectories = $createdDirs
        Message = if ($success) { "All directories created successfully" } else { "Failed to create some directories" }
    }
}

# Function to show directory check results and handle creation
function Show-DirectoryCheck {
    param(
        [object]$DirectoryResult
    )
    
    if ($DirectoryResult.AllExist) {
        # All directories exist - show success
        $successContent = @(
            "",
            "                        [OK] DIRECTORIES READY",
            "",
            "                    All required directories exist:",
            ""
        )
        
        foreach ($dir in $DirectoryResult.Directories) {
            $relativePath = $dir.Path.Replace($env:USERPROFILE, "~")
            $successContent += "                  ✓ $relativePath"
        }
        
        $successContent += @(
            "",
            "                         Ready to proceed!",
            "",
            "---",
            "",
            "                      Press any key to continue",
            ""
        )
        
        Clear-Host
        Write-Host ("=" * 80) -ForegroundColor Cyan
        $title = "DIRECTORY CHECK - SUCCESS"
        $padding = (80 - $title.Length - 2) / 2
        $leftPadding = [int][Math]::Floor($padding)
        $rightPadding = [int][Math]::Ceiling($padding)
        Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Green
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        foreach ($line in $successContent) {
            if ($line -eq "---") {
                Write-Host ("-" * 80) -ForegroundColor Gray
            } elseif ($line.Contains("[OK] DIRECTORIES READY")) {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
            } elseif ($line.Contains("✓")) {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
            } else {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
            }
        }
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        $key = Wait-ForUserInput -PromptText ">> Press any key to continue"
        return $true
    }
    
    # Some directories are missing - show creation prompt
    $missingDirs = $DirectoryResult.Directories | Where-Object { -not $_.Exists }
    
    $createContent = @(
        "",
        "                        [!] DIRECTORIES REQUIRED",
        "",
        "                   Maps4fs requires the following directories",
        "                      for Docker volume mounting:",
        ""
    )
    
    foreach ($dir in $missingDirs) {
        $relativePath = $dir.Path.Replace($env:USERPROFILE, "~")
        $createContent += "                  ✗ $relativePath"
        $createContent += "                    ($($dir.Description))"
    }
    
    $createContent += @(
        "",
        "                    These directories will be automatically",
        "                       mounted by Docker containers.",
        "",
        "---",
        "",
        "                 Y - Create missing directories",
        "                 N - Exit setup",
        ""
    )
    
    Clear-Host
    Write-Host ("=" * 80) -ForegroundColor Cyan
    $title = "DIRECTORY SETUP REQUIRED"
    $padding = (80 - $title.Length - 2) / 2
    $leftPadding = [int][Math]::Floor($padding)
    $rightPadding = [int][Math]::Ceiling($padding)
    Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Yellow
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    foreach ($line in $createContent) {
        if ($line -eq "---") {
            Write-Host ("-" * 80) -ForegroundColor Gray
        } elseif ($line.Contains("[!] DIRECTORIES REQUIRED")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Yellow
        } elseif ($line.Contains("✗")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Red
        } elseif ($line.Contains("Y - Create") -or $line.Contains("N - Exit")) {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Yellow
        } else {
            $contentLength = $line.Length
            $padding = 80 - $contentLength - 2
            Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
        }
    }
    Write-Host ("=" * 80) -ForegroundColor Cyan
    
    # Wait for user choice
    do {
        $key = Wait-ForUserInput -PromptText ">> Create directories (Y/N)"
        $choice = $key.Character.ToString().ToUpper()
        
        if ($choice -eq "Y") {
            # Create missing directories
            Write-Host ""
            Write-Host "Creating missing directories..." -ForegroundColor Yellow
            
            $createResult = New-RequiredDirectories -MissingDirectories $missingDirs
            
            # Show creation results
            $resultContent = @("", "                          DIRECTORY CREATION RESULTS", "")
            
            if ($createResult.Success) {
                $resultContent += "                    [OK] All directories created successfully"
                $resultContent += ""
                
                foreach ($dirPath in $createResult.CreatedDirectories) {
                    $relativePath = $dirPath.Replace($env:USERPROFILE, "~")
                    $resultContent += "                  ✓ Created: $relativePath"
                }
                
                $resultContent += @(
                    "",
                    "                         Ready to proceed!",
                    "",
                    "---",
                    "",
                    "                      Press any key to continue",
                    ""
                )
                $titleColor = "Green"
                $titleText = "DIRECTORIES CREATED"
            } else {
                $resultContent += @(
                    "                   [!] Failed to create some directories",
                    "",
                    "                     Please create them manually or",
                    "                      run the wizard as administrator",
                    "",
                    "---",
                    "",
                    "                 Y - Continue anyway",
                    "                 N - Exit wizard",
                    ""
                )
                $titleColor = "Yellow"
                $titleText = "PARTIAL SUCCESS"
            }
            
            Clear-Host
            Write-Host ("=" * 80) -ForegroundColor Cyan
            $title = $titleText
            $padding = (80 - $title.Length - 2) / 2
            $leftPadding = [int][Math]::Floor($padding)
            $rightPadding = [int][Math]::Ceiling($padding)
            Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor $titleColor
            Write-Host ("=" * 80) -ForegroundColor Cyan
            
            foreach ($line in $resultContent) {
                if ($line -eq "---") {
                    Write-Host ("-" * 80) -ForegroundColor Gray
                } elseif ($line.Contains("[OK]")) {
                    $contentLength = $line.Length
                    $padding = 80 - $contentLength - 2
                    Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
                } elseif ($line.Contains("[!]")) {
                    $contentLength = $line.Length
                    $padding = 80 - $contentLength - 2
                    Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Yellow
                } elseif ($line.Contains("✓")) {
                    $contentLength = $line.Length
                    $padding = 80 - $contentLength - 2
                    Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
                } else {
                    $contentLength = $line.Length
                    $padding = 80 - $contentLength - 2
                    Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
                }
            }
            Write-Host ("=" * 80) -ForegroundColor Cyan
            
            if ($createResult.Success) {
                $key = Wait-ForUserInput -PromptText ">> Press any key to continue"
                return $true
            } else {
                # Partial success - ask if continue
                do {
                    $continueKey = Wait-ForUserInput -PromptText ">> Continue anyway (Y/N)"
                    $continueChoice = $continueKey.Character.ToString().ToUpper()
                    
                    if ($continueChoice -eq "Y") {
                        return $true
                    } elseif ($continueChoice -eq "N") {
                        return $false
                    } else {
                        Write-Host "Please press Y or N" -ForegroundColor Red
                        Start-Sleep -Seconds 1
                    }
                } while ($true)
            }
            
        } elseif ($choice -eq "N") {
            return $false  # Exit
        } else {
            Write-Host "Please press Y or N" -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    } while ($true)
}

# Function to download docker-compose.yml and start deployment
function Start-Maps4fsDeployment {
    try {
        $deployContent = @(
            "",
            "                        STARTING MAPS4FS DEPLOYMENT",
            "",
            "                    The wizard will now download the latest",
            "                      Docker Compose configuration and",
            "                         launch Maps4fs containers",
            "",
            "                           This will:",
            "                    1. Download docker-compose.yml from GitHub",
            "                    2. Pull the latest Maps4fs Docker images",
            "                    3. Start the frontend and backend services",
            "                    4. Open Maps4fs in your browser",
            "",
            "---",
            "",
            "                    Press Y to start deployment or N to exit",
            ""
        )
        
        Show-Frame -Content $deployContent -Title "DEPLOYMENT READY"
        
        do {
            $key = Wait-ForUserInput -PromptText ">> Start deployment (Y/N)"
            $choice = $key.Character.ToString().ToUpper()
            
            if ($choice -eq "Y") {
                # Download docker-compose.yml
                $downloadContent = @(
                    "",
                    "                        DOWNLOADING CONFIGURATION",
                    "",
                    "                     Downloading docker-compose.yml from",
                    "                     https://github.com/iwatkot/maps4fs",
                    "",
                    "                           Please wait...",
                    ""
                )
                Show-Frame -Content $downloadContent -Title "DOWNLOAD IN PROGRESS"
                
                Write-Host ""
                Write-Host ">> Downloading docker-compose.yml..." -ForegroundColor Yellow
                
                try {
                    $composeUrl = "https://raw.githubusercontent.com/iwatkot/maps4fs/main/docker-compose.yml"
                    $composePath = ".\docker-compose.yml"
                    
                    # Download compose file
                    Invoke-WebRequest -Uri $composeUrl -OutFile $composePath -UseBasicParsing
                    
                    if (Test-Path $composePath) {
                        Write-Host ">> Docker Compose configuration downloaded successfully" -ForegroundColor Green
                        
                        # Start deployment
                        $startContent = @(
                            "",
                            "                        STARTING CONTAINERS",
                            "",
                            "                     Starting Maps4fs with Docker Compose",
                            "",
                            "                    This may take a few minutes as Docker",
                            "                      downloads the required images...",
                            "",
                            "                           Please wait...",
                            ""
                        )
                        Show-Frame -Content $startContent -Title "DEPLOYMENT STARTING"
                        
                        Write-Host ""
                        Write-Host ">> Starting Maps4fs containers with Docker Compose..." -ForegroundColor Yellow
                        
                        # Execute docker-compose up -d
                        $composeOutput = docker-compose up -d 2>&1
                        
                        if ($LASTEXITCODE -eq 0) {
                            Write-Host ">> Maps4fs containers started successfully!" -ForegroundColor Green
                            
                            # Wait a moment for containers to fully start
                            Write-Host ">> Waiting for services to be ready..." -ForegroundColor Yellow
                            Start-Sleep -Seconds 5
                            
                            return @{
                                Success = $true
                                Message = "Maps4fs deployment completed successfully"
                                Output = $composeOutput
                            }
                        } else {
                            return @{
                                Success = $false
                                Message = "Failed to start containers"
                                Output = $composeOutput
                                Error = "Docker Compose failed with exit code $LASTEXITCODE"
                            }
                        }
                    } else {
                        throw "Downloaded compose file not found"
                    }
                } catch {
                    return @{
                        Success = $false
                        Message = "Failed to download docker-compose.yml"
                        Output = $null
                        Error = $_.Exception.Message
                    }
                }
            } elseif ($choice -eq "N") {
                return @{
                    Success = $false
                    Message = "Deployment cancelled by user"
                    Output = $null
                    Error = $null
                }
            } else {
                Write-Host "Please press Y or N" -ForegroundColor Red
                Start-Sleep -Seconds 1
            }
        } while ($true)
        
    } catch {
        return @{
            Success = $false
            Message = "Error during deployment process"
            Output = $null
            Error = $_.Exception.Message
        }
    }
}

# Function to show deployment results and launch browser
function Show-DeploymentResults {
    param(
        [object]$DeploymentResult
    )
    
    if ($DeploymentResult.Success) {
        # Success - show completion message and launch browser
        $successContent = @(
            "",
            "                        [OK] DEPLOYMENT SUCCESSFUL",
            "",
            "                     Maps4fs is now running locally!",
            "",
            "                         Service endpoints:",
            "                      * Frontend: http://localhost:3000",
            "                      * Backend:  http://localhost:8000",
            "",
            "                    Opening Maps4fs in your browser...",
            "",
            "---",
            "",
            "                    To stop Maps4fs later, run:",
            "                         docker-compose down",
            "",
            "                      Press any key to finish setup",
            ""
        )
        
        Clear-Host
        Write-Host ("=" * 80) -ForegroundColor Cyan
        $title = "SETUP COMPLETE"
        $padding = (80 - $title.Length - 2) / 2
        $leftPadding = [int][Math]::Floor($padding)
        $rightPadding = [int][Math]::Ceiling($padding)
        Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Green
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        foreach ($line in $successContent) {
            if ($line -eq "---") {
                Write-Host ("-" * 80) -ForegroundColor Gray
            } elseif ($line.Contains("[OK] DEPLOYMENT SUCCESSFUL")) {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
            } elseif ($line.Contains("docker-compose down")) {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Yellow
            } else {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
            }
        }
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        # Launch browser
        Write-Host ""
        Write-Host ">> Opening Maps4fs in your default browser..." -ForegroundColor Yellow
        
        try {
            Start-Process "http://localhost:3000"
            Write-Host ">> Browser launched successfully!" -ForegroundColor Green
        } catch {
            Write-Host ">> Could not automatically open browser" -ForegroundColor Yellow
            Write-Host "   Please manually open: http://localhost:3000" -ForegroundColor Yellow
        }
        
        # Wait for user to finish
        $key = Wait-ForUserInput -PromptText ">> Press any key to finish setup"
        return $true
        
    } else {
        # Failure - show error message
        $errorContent = @(
            "",
            "                        [X] DEPLOYMENT FAILED",
            "",
            "                    Failed to start Maps4fs containers",
            "",
            "                              Error details:",
            "                     $($DeploymentResult.Message)",
            ""
        )
        
        if ($DeploymentResult.Error) {
            $errorContent += "                     $($DeploymentResult.Error)"
            $errorContent += ""
        }
        
        $errorContent += @(
            "                           Troubleshooting:",
            "",
            "                   1. Ensure Docker Desktop is running",
            "                   2. Check internet connection for image downloads",
            "                   3. Verify ports 3000 and 8000 are available",
            "                   4. Try running manually: docker-compose up -d",
            "",
            "---",
            "",
            "                       Press any key to exit",
            ""
        )
        
        Clear-Host
        Write-Host ("=" * 80) -ForegroundColor Cyan
        $title = "DEPLOYMENT FAILED"
        $padding = (80 - $title.Length - 2) / 2
        $leftPadding = [int][Math]::Floor($padding)
        $rightPadding = [int][Math]::Ceiling($padding)
        Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Red
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        foreach ($line in $errorContent) {
            if ($line -eq "---") {
                Write-Host ("-" * 80) -ForegroundColor Gray
            } elseif ($line.Contains("[X] DEPLOYMENT FAILED")) {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Red
            } else {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
            }
        }
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        $key = Wait-ForUserInput -PromptText ">> Press any key to exit"
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
    
    # Step 4: Test if Docker is actually running
    Write-Host "Testing Docker functionality..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
    
    $dockerRunResult = Test-DockerRunning
    $dockerRunContinue = Show-DockerRunningStatus -DockerRunResult $dockerRunResult
    
    if (-not $dockerRunContinue) {
        Show-Frame -Content @("", "                              Setup aborted", "") -Title "GOODBYE"
        Start-Sleep -Seconds 2
        exit 0
    }
    
    # Step 5: Check for existing maps4fs containers
    Write-Host "Checking for existing containers..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
    
    $containerResult = Test-ExistingContainers
    $containerContinue = Show-ExistingContainers -ContainerResult $containerResult
    
    if (-not $containerContinue) {
        Show-Frame -Content @("", "                              Setup aborted", "") -Title "GOODBYE"
        Start-Sleep -Seconds 2
        exit 0
    }
    
    # Step 6: Check required ports availability
    Write-Host "Checking port availability..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
    
    $portResult = Test-RequiredPorts
    $portContinue = Show-PortAvailability -PortResult $portResult
    
    if (-not $portContinue) {
        Show-Frame -Content @("", "                       Ports are required for maps4fs", "", "                      Please free ports and try again", "") -Title "GOODBYE"
        Start-Sleep -Seconds 3
        exit 1
    }
    
    # Step 7: Check and create required directories
    Write-Host "Checking required directories..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
    
    $directoryResult = Test-RequiredDirectories
    $directoryContinue = Show-DirectoryCheck -DirectoryResult $directoryResult
    
    if (-not $directoryContinue) {
        Show-Frame -Content @("", "                         Directory setup cancelled", "", "                      Required directories are needed", "") -Title "GOODBYE"
        Start-Sleep -Seconds 3
        exit 1
    }
    
    # Step 8: Deploy Maps4fs with Docker Compose
    Write-Host "Preparing Maps4fs deployment..." -ForegroundColor Yellow
    Start-Sleep -Seconds 1
    
    $deploymentResult = Start-Maps4fsDeployment
    $deploymentSuccess = Show-DeploymentResults -DeploymentResult $deploymentResult
    
    if ($deploymentSuccess) {
        # Final success message
        $finalContent = @(
            "",
            "                    MAPS4FS SETUP WIZARD COMPLETED",
            "",
            "                     Thank you for using Maps4fs!",
            "",
            "                      Maps4fs is now running at:",
            "                       http://localhost:3000",
            "",
            "                         Support the project:",
            "                    ⭐ Star us on GitHub: github.com/iwatkot/maps4fs",
            "                    💬 Join our community discussions",
            "                    🐛 Report issues and suggest features",
            "",
            "                        Enjoy creating your maps!",
            ""
        )
        
        Clear-Host
        Write-Host ("=" * 80) -ForegroundColor Cyan
        $title = "SETUP WIZARD COMPLETE"
        $padding = (80 - $title.Length - 2) / 2
        $leftPadding = [int][Math]::Floor($padding)
        $rightPadding = [int][Math]::Ceiling($padding)
        Write-Host (("=" * $leftPadding) + " " + $title + " " + ("=" * $rightPadding)) -ForegroundColor Green
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        foreach ($line in $finalContent) {
            if ($line.Contains("⭐") -or $line.Contains("💬") -or $line.Contains("🐛")) {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Yellow
            } elseif ($line.Contains("http://localhost:3000")) {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Green
            } else {
                $contentLength = $line.Length
                $padding = 80 - $contentLength - 2
                Write-Host ("|" + $line + (" " * $padding) + "|") -ForegroundColor Cyan
            }
        }
        Write-Host ("=" * 80) -ForegroundColor Cyan
        
        exit 0
    } else {
        # Deployment failed
        Show-Frame -Content @("", "                        Setup completed with errors", "", "                     Please check the error messages above", "") -Title "SETUP FINISHED"
        Start-Sleep -Seconds 3
        exit 1
    }
    
} catch {
    Write-Host "An error occurred: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
