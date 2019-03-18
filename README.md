# therm

Arduino thermostat.

### To Do

* Proper multi-zone filtering
* Scheduled control
* Schedule editing in app
* Schedule editing from device
* Color chart by whether heat was on/off

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
add to `/etc/xdg/lxsession/LXDE-pi/autostart`:
```bash
@/bin/bash /home/pi/devel/therm/run_all.sh
```

