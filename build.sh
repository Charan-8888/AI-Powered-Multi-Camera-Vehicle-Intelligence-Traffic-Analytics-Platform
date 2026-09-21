#!/usr/bin/env bash
set -o errexit

pip install -r backend/requirements.txt
python backend/manage.py collectstatic --noinput
python backend/manage.py migrate --noinput
python backend/manage.py seed_demo_data
