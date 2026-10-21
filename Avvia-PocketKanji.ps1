param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$appFile = Join-Path $PSScriptRoot 'PocketKanji.html'
$listener = $null
$baseUrl = $null
try {
    if (-not (Test-Path -LiteralPath $appFile)) { throw 'PocketKanji.html non trovato nella cartella del programma.' }
    foreach ($port in 8765..8775) {
        $candidate = "http://127.0.0.1:$port/"
        try {
            $request = [System.Net.WebRequest]::Create($candidate + '__pocketkanji')
            $request.Proxy = $null
            $request.Timeout = 400
            $response = $request.GetResponse()
            $reader = New-Object System.IO.StreamReader($response.GetResponseStream())
            $body = $reader.ReadToEnd()
            $reader.Dispose()
            $response.Dispose()
            if ($body -eq 'PocketKanji:v0.1') {
                if (-not $NoBrowser) { Start-Process $candidate }
                Write-Output "PocketKanji gia avviato: $candidate"
                exit 0
            }
        } catch { }
        $candidateListener = New-Object System.Net.Sockets.TcpListener([System.Net.IPAddress]::Loopback, $port)
        try {
            $candidateListener.Start()
            $listener = $candidateListener
            $baseUrl = $candidate
            break
        } catch { $candidateListener.Stop() }
    }
    if ($null -eq $listener) { throw 'Le porte locali 8765-8775 sono occupate. Riprova dopo aver chiuso altre applicazioni locali.' }
    $shortcut = "[InternetShortcut]`r`nURL=$baseUrl`r`n"
    [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot 'Apri PocketKanji.url'), $shortcut)
    Write-Output "PocketKanji avviato: $baseUrl"
    if (-not $NoBrowser) { Start-Process $baseUrl }
    $lastRequest = [DateTime]::UtcNow
    while (([DateTime]::UtcNow - $lastRequest).TotalHours -lt 8) {
        if (-not $listener.Pending()) { Start-Sleep -Milliseconds 100; continue }
        $client = $listener.AcceptTcpClient()
        try {
            $client.ReceiveTimeout = 3000
            $client.SendTimeout = 3000
            $stream = $client.GetStream()
            $buffer = New-Object byte[] 8192
            $length = $stream.Read($buffer, 0, $buffer.Length)
            if ($length -eq 0) { continue }
            $firstLine = ([System.Text.Encoding]::ASCII.GetString($buffer, 0, $length) -split "`r`n")[0]
            $path = ($firstLine -split ' ')[1]
            $lastRequest = [DateTime]::UtcNow
            $status = '200 OK'
            $contentType = 'text/plain; charset=utf-8'
            if ($path -eq '/' -or $path -eq '/PocketKanji.html') {
                $payload = [System.IO.File]::ReadAllBytes($appFile)
                $contentType = 'text/html; charset=utf-8'
            } elseif ($path -eq '/__pocketkanji') {
                $payload = [System.Text.Encoding]::UTF8.GetBytes('PocketKanji:v0.1')
            } else {
                $status = '404 Not Found'
                $payload = [System.Text.Encoding]::UTF8.GetBytes('Not found')
            }
            $header = [System.Text.Encoding]::ASCII.GetBytes("HTTP/1.1 $status`r`nContent-Type: $contentType`r`nContent-Length: $($payload.Length)`r`nConnection: close`r`nCache-Control: no-store`r`nX-Content-Type-Options: nosniff`r`n`r`n")
            $stream.Write($header, 0, $header.Length)
            $stream.Write($payload, 0, $payload.Length)
            $stream.Flush()
        } catch { } finally { $client.Close() }
    }
} catch {
    $message = "Impossibile avviare PocketKanji: " + $_.Exception.Message
    [System.IO.File]::WriteAllText((Join-Path $PSScriptRoot 'PocketKanji-errore.txt'), $message)
    if (-not $NoBrowser) {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show($message, 'PocketKanji') | Out-Null
    }
    Write-Error $message
} finally { if ($null -ne $listener) { $listener.Stop() } }
