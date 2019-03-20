# therm

A Raspberry Pi thermostat control app

![Pi Model B with screen displaying thermostat](therm/static/img/3b_with_screen.jpg?raw=true)
![Dashboard in web browser](therm/static/img/dashboard_screenshot.jpg?raw=true)
![](therm/static/img/mag_wire_shield.jpg?raw=true)
![](therm/static/img/zero_with_shield_front.jpg?raw=true)


### Install

On the raspi you'll need `libblas` before installing scipy:
```bash
sudo apt-get install libblas-dev libatlas-base-dev rpi.gpio

```

This project uses python 3. It's recommended that you use virtualenvwrapper.
On raspbian, do:
```bash
sudo pip3 install virtualenv virtualenvwrapper
```

Add the following to ~/.bash_profile:
```bash
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
source /usr/local/bin/virtualenvwrapper.sh
```

Then:
```bash
mkvirtualenv therm
workon therm

```
Then install python requirements:
```bash
pip install -r requirements.txt -r requirements-device.txt
```
This will probably take a while (1-2hr on a RasPi zero); some of the requirements do
not have wheels available for raspi, and therefore will be built from source.

To run the tests (requires python 3.6, specifically for `assert_called_once`):
```bash
pip install -r requirements-test.txt
pytest

```


### Configuration

Therm uses a database to store temperature observations and thermostat state.
Any DB that SQLALchemy can talk to works. To configure your DB, set the
following environment variables (or handcode them in `therm.settings` if you're
feeling bold):
```bash
export THERM_DB_URL=thermdb.cln2j9a8fio32eu.us-east-1.rds.amazonaws.com
export THERM_DB_UNAME=thermuser
export THERM_DB_PASS=correct-horse-battery-staple
```

If you want to send status messages to SQS using `flask poll --to-sqs`, you'll
need to [configure boto3](https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html).

#### Per-device hardware config



### Run

The full thermostat consists of three processes: a polling loop, a web server,
and a browser displaying the web UI on the raspi screen.

To start the polling loop:
```bash
FLASK_APP=therm flask poll
```

The polling loop reads the temp sensor and write samples to the DB. It also
looks at the latest `State` in the DB, and if the state represents a thermostat
"hold" temperature, it will enable/disable the heat relay. 

The polling loop also handles button presses (TODO: explain State)

To start the web server:
```bash
FLASK_APP=therm flask run
```

To start Chromium in 320x240 kiosk mode on display `0`:
```bash
./kiosk.sh
```

### Testing

Running any of this in an environment without the raspberry pi library (e.g. your laptop)
will fallback to `fake-rpi`, which provides fake sensor inputs and GPIO outputs to
the program, as well as dumping debug information to the console.


### Shell

Jupyter is included in test requirements, see 
https://blog.sneawo.com/blog/2017/06/27/how-to-use-jupyter-notebooks-with-flask-app/
for how to import your flask app into a jupyter notebook (and for some reason use docker if you want.)


### Autostart on raspi:

I currently have two devices: a raspi Zero without a screen running the relay and temp sensor,
and a raspi B+ with a 2.2" screen running the web UI and buttons


To run the web UI on startup on the b+, add to `/etc/xdg/lxsession/LXDE-pi/autostart`:
```bash
@/bin/bash /home/pi/devel/therm/run_kiosk.sh
```

To run relay and sensor on the zero, add to `/etc/rc.local`:
```bash
su pi /home/pi/devel/therm/run_temp.sh
```

In this setup, there are no buttons (pi B TFT hat has buttons, but they run in poll loop,
so not enabled in this mode.)

To run everything on a single device, add to `/etc/xdg/lxsession/LXDE-pi/autostart`:
```bash
@/bin/bash /home/pi/devel/therm/run_all.sh
```

### uWSGI + nginx

Install nginx and uwsgi globally (make sure you're using python 3 install!):
```bash
sudo pip3 install uwsgi
sudo apt-get install nginx
```

Add your site config in `/etc/nginx/sites-available/therm.conf`:
```
server {
	listen 80;
	server_name pi.local;

	location / {
	    include uwsgi_params;
	    uwsgi_pass unix:/tmp/uwsgi/therm.sock;
	}
}
```

Create a systemd service for uwsgi in `/etc/systemd/system/uwsgi.service`
```
[Unit]
Description=uWSGI instance to serve therm

[Service]
ExecStartPre=-/bin/bash -c 'mkdir -p /tmp/uwsgi; chown www-data /tmp/uwsgi'
ExecStart=/bin/bash -c 'cd /home/pi/devel/therm; source /home/pi/.virtualenvs/therm/bin/activate; uwsgi --ini uwsgi.ini --logto /var/log/therm.log'

[Install]
WantedBy=multi-user.target
```

Test it:
```bash
sudo systemctl start uwsgi
```

Launch nginx and make sure everything's working:
```bash
sudo service nginx start
```

If everything works, you can have nginx and uwsgi launch on boot:
```bash
$ sudo systemctl enable nginx
$ sudo systemctl enable uwsgi

```
