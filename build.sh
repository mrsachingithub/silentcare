#!/usr/bin/env bash
# Exit on error
set -o errexit

pip install -r requirements.txt

python init_db.py
