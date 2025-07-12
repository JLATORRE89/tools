@echo off
echo Collecting Active Ports with netstat.
netstat -b > %COMPUTERNAME%ports.txt
echo Collecting hostname to be used as a reference.
copy c:\windows\system32\drivers\etc\hosts %COMPUTERNAME%host.txt
echo Moving files to secure location.
REM Either add map drive or store in secure directory for future collection.
mkdir C:\SecureStuff
move %COMPUTERNAME%host.txt C:\SecureStuff
cd C:\SecureStuff
REM Will require powershell scripts enabled on the system or a wrapper for creating a zip file.
echo Attempting to create Zip file.
powershell Compress-Archive . ppsm.zip
echo All work complete.
