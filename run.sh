#!/usr/bin/env bash
# Run the CLI with the project conda env (no need to activate manually).
# Use conda activate + exec so python keeps the terminal (progress bar works).
# conda run buffers output and does not show progress in real time.
cd "$(dirname "$0")"
eval "$(conda shell.bash hook)"
conda activate process-frame-sheet
exec python -u cli.py "$@"
