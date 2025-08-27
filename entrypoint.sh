#!/bin/bash

set -e  # Cancel if error raises

python init.py "$OWNER_UUID"

python bot.py

