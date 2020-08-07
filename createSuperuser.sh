#!/bin/bash
#This script makes a django superuser with username 'admin' and password of whatever is at
#/run/secrets/cvatAdminPassword, which is handled by docker secrets.

python3 ./manage.py shell -c "
from django.contrib.auth.models import User;
User.objects.create_superuser('admin', 'a@b.com', '$(cat /run/secrets/cvatAdminPassword)')
"
