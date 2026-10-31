#!/bin/bash
pip install -r requirements.txt
python QLVB/manage.py collectstatic --noinput --clear
