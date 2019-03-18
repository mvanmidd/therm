source /home/pi/.bash_profile
source /home/pi/.bashrc

cd /home/pi/devel/therm
workon therm
FLASK_APP=therm THERM_ENV=Production THERM_DEVICE=Zero flask poll --to-sqs --force
