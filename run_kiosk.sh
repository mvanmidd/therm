source /home/pi/.bash_profile
source /home/pi/.bashrc

cd /home/pi/devel/therm
workon therm
THERM_ENV=Production flask run --host 0.0.0.0 2>&1 > /dev/null &
/home/pi/devel/therm/kiosk.sh &
