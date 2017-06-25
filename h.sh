#!/bin/bash

apt install mysql-server
apt install mysql-client 
mysqladmin -u root password root
mysql -u root -p < m.sql
apt install git
git clone https://github.com/burmistrovm/dbserver
cd dbserver/
mysql -u django -p24081994 < db_scheme.sql 
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py 
rm get-pip.py 
pip install django
pip install pattern
pip install patterns
pip install requests
apt-get install python-mysqldb
apt install vim
./manage.py makemigrations
./manage.py migrate
apt install tree
apt install gunicorn
gunicorn dbserver.wsgi:application --bind 0.0.0.0:8000
