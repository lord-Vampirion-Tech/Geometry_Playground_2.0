param(
    [Parameter(Mandatory = $true)]
    [string]$BuildScript,

    [Parameter(Mandatory = $true)]
    [string]$LogFile
)

$ErrorActionPreference = "Stop"

Add-Type -TypeDefinition @'
using System;
using System.Diagnostics;
using System.IO;
using System.Text;
using System.Threading;

public static class BuildOutputPump
{
    private static readonly object WriteLock = new object();

    public static void Pump(Process process, string logFile)
    {
        using (var log = new StreamWriter(
            new FileStream(logFile, FileMode.Append, FileAccess.Write, FileShare.Read),
            new UTF8Encoding(false),
            65536))
        {
            var stdoutThread = new Thread(() =>
                CopyChunks(process.StandardOutput, Console.Out, log));
            var stderrThread = new Thread(() =>
                CopyChunks(process.StandardError, Console.Error, log));

            stdoutThread.IsBackground = true;
            stderrThread.IsBackground = true;

            stdoutThread.Start();
            stderrThread.Start();

            process.WaitForExit();

            stdoutThread.Join();
            stderrThread.Join();

            lock (WriteLock)
            {
                log.Flush();
                Console.Out.Flush();
                Console.Error.Flush();
            }
        }
    }

    private static void CopyChunks(StreamReader input, TextWriter console, StreamWriter log)
    {
        char[] buffer = new char[8192];
        int count;

        while ((count = input.Read(buffer, 0, buffer.Length)) > 0)
        {
            lock (WriteLock)
            {
                console.Write(buffer, 0, count);
                console.Flush();

                log.Write(buffer, 0, count);
                log.Flush();
            }
        }
    }
}
'@

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
$processStarted = $false

try {
    if (-not $process.Start()) {
        throw "Could not start the build process."
    }
    $processStarted = $true

    [BuildOutputPump]::Pump($process, $LogFile)
    exit $process.ExitCode
}
catch {
    $message = "Build logger error: " + $_.Exception.Message
    [Console]::Error.WriteLine($message)

    try {
        [System.IO.File]::AppendAllText(
            $LogFile,
            $message + [Environment]::NewLine,
            (New-Object System.Text.UTF8Encoding($false))
        )
    }
    catch {
        [Console]::Error.WriteLine("Could not write the logger error to the log file.")
    }

    if ($processStarted -and -not $process.HasExited) {
        $process.Kill()
        $process.WaitForExit()
    }

    exit 1
}
finally {
    $process.Dispose()
}
