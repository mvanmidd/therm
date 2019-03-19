source /home/pi/.bash_profile
source /home/pi/.bashrc

cd /home/pi/devel/therm
workon therm
FLASK_APP=therm THERM_ENV=Production THERM_DEVICE=Zero nohup flask poll --to-sqs --force 2>&1 >/home/pi/server.log &
