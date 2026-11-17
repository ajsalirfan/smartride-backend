@echo off
cd /d "C:\Users\ajsal\OneDrive\Documents\Smart_Ride"
call myenv\Scripts\activate
cd smartride_backend
echo Smart Ride environment activated!
python manage.py runserver
