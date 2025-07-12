#!/bin/bash
echo "Collecting port data."
ss -pl > /var/log/audit/ppsm.log
echo "Collecting host file."
cp  /etc/hosts /var/log/audit/host.log
echo "Generating archive for collection."
tar -cvf ppsm.tgz host.log ppsm.log
echo "Cleaning up files."
rm /var/log/audit/ppsm.log
rm /var/log/audit/host.log
echo "ppsm.tgz will be picked up by another process."
echo "All work complete."
