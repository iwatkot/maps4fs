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
    try {
        Write-Host ">> Testing Docker with hello-world container..." -ForegroundColor Yellow
        
        # Run hello-world container and capture output
        $dockerOutput = docker run --rm hello-world 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ">> Docker is running correctly!" -ForegroundColor Green
            
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
                                
                                $retestResult = Test-DockerRunning
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
    
    # Step 5: Continue with next steps...
    Show-Frame -Content @("", "                     Docker is ready and running!", "", "                        ... (More steps to implement)", "") -Title "SETUP IN PROGRESS"
    
    # Placeholder for next steps
    Write-Host ""
    Write-Host "Next steps would be implemented here..." -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    
} catch {
    Write-Host "An error occurred: $($_.Exception.Message)" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}
