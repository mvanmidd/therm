source /home/pi/.bash_profile
source /home/pi/.bashrc

cd /home/pi/devel/therm
workon therm
FLASK_APP=therm THERM_ENV=Production THERM_DEVICE=Buttons nohup flask poll --no-reset &
nohup /home/pi/devel/therm/kiosk.sh &
