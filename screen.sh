gpio -g mode 18 pwm
gpio pwmc 1000
if [ $1 = "off" ]; then
	gpio -g pwm 18 0
elif [ $1 = "dim" ]; then
	gpio -g pwm 18 30
elif [ $1 = "on" ]; then
	gpio -g pwm 18 1000
fi
