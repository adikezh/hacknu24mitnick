#!/bin/bash

source /home/oysyn/codebase/antiplagiatkz-app/venv/bin/activate
cd /home/oysyn/codebase/antiplagiatkz-app
exec celery -A core worker --loglevel=info

