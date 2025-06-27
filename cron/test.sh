#!/bin/bash

# Script to test cron automated task
# Writes the current date and time in a new line in logs.txt
# Add the worker with this line for a timestamp each minute
#
# * 6 * * * cd /path/to/repo/ && ./cron/test.sh
#

echo "$(date)" >> ./cron/logs.txt