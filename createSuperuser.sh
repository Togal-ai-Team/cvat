#!/bin/bash
#This script makes a django superuser with username 'admin' and password of whatever is at
#/run/secrets/cvatAdminPassword, which is handled by docker secrets.

python3 ./manage.py shell -c "
username='admin'
email='a@b.com'

from django.contrib.auth.models import User;
if User.objects.filter(username=username).count()==0:
    User.objects.create_superuser('admin', 'a@b.com', '$(cat /run/secrets/cvatAdminPassword)')
    print('Superuser created: admin')
else:
    print('Superuser already exists.  Skipping creation.')
"
