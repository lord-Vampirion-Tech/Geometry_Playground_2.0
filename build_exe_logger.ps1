param(
    [Parameter(Mandatory = $true)]
    [string]$BuildScript,

    [Parameter(Mandatory = $true)]
    [string]$LogFile
)

$ErrorActionPreference = "Stop"

$process = New-Object System.Diagnostics.Process
$startInfo = New-Object System.Diagnostics.ProcessStartInfo

$startInfo.FileName = $env:ComSpec
$startInfo.Arguments = '/d /c ""' + $BuildScript + '" __BUILD"'
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $false
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
$startInfo.StandardOutputEncoding = [Console]::OutputEncoding
$startInfo.StandardErrorEncoding = [Console]::OutputEncoding

$process.StartInfo = $startInfo

$writeLock = New-Object Object
$logEncoding = New-Object System.Text.UTF8Encoding($false)

$outputHandler = {
    param($sender, $eventArgs)

    if ($null -eq $eventArgs.Data) {
        return
    }

    [System.Threading.Monitor]::Enter($writeLock)
    try {
        [Console]::Out.WriteLine($eventArgs.Data)
        [System.IO.File]::AppendAllText(
            $LogFile,
            $eventArgs.Data + [Environment]::NewLine,
            $logEncoding
        )
    }
    finally {
        [System.Threading.Monitor]::Exit($writeLock)
    }
}.GetNewClosure()

$errorHandler = {
    param($sender, $eventArgs)

    if ($null -eq $eventArgs.Data) {
        return
    }

    [System.Threading.Monitor]::Enter($writeLock)
    try {
        [Console]::Error.WriteLine($eventArgs.Data)
        [System.IO.File]::AppendAllText(
            $LogFile,
            $eventArgs.Data + [Environment]::NewLine,
            $logEncoding
        )
    }
    finally {
        [System.Threading.Monitor]::Exit($writeLock)
    }
}.GetNewClosure()

try {
    $process.add_OutputDataReceived($outputHandler)
    $process.add_ErrorDataReceived($errorHandler)

    if (-not $process.Start()) {
        throw "Could not start the build process."
    }

    $process.BeginOutputReadLine()
    $process.BeginErrorReadLine()

    $process.WaitForExit()
    $process.WaitForExit()

    exit $process.ExitCode
}
catch {
    $message = "Build logger error: " + $_.Exception.Message
    [Console]::Error.WriteLine($message)

    try {
        [System.IO.File]::AppendAllText(
            $LogFile,
            $message + [Environment]::NewLine,
            $logEncoding
        )
    }
    catch {
        [Console]::Error.WriteLine("Could not write the logger error to the log file.")
    }

    exit 1
}
finally {
    $process.Dispose()
}
