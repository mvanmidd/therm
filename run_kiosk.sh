source /home/pi/.bash_profile
source /home/pi/.bashrc

cd /home/pi/devel/therm
workon therm
FLASK_APP=therm THERM_ENV=Production nohup flask run --host 0.0.0.0 2>&1 > /dev/null &
nohup /home/pi/devel/therm/kiosk.sh &
