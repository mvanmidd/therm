source /home/pi/.bash_profile
source /home/pi/.bashrc

cd /home/pi/devel/therm
workon therm
/home/pi/devel/therm/kiosk.sh &
THERM_ENV=Production flask run --host 0.0.0.0 &
THERM_ENV=Production flask poll --to-sqs --force
