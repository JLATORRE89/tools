@echo off
echo Collecting Active Ports with netstat.
netstat -b > %COMPUTERNAME%ports.txt
echo Collecting hostname to be used as a reference.
copy c:\windows\system32\drivers\etc\hosts %COMPUTERNAME%hostfile.txt
echo Moving files to secure location.
REM Either add map drive or store in secure directory for future collection.
mkdir C:\SecureStuff
move %COMPUTERNAME%hostfile.txt C:\SecureStuff
echo All work complete.
