@echo off
title ApplyPilot
ssh -t localnet "cd /ai/ApplyPilot && source .venv/bin/activate && applypilot doctor; echo; echo Ready. Try: applypilot run, applypilot run score, applypilot doctor; exec bash -l"
