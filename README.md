# therm

Arduino thermostat.

### Install

Requires some aruino libraries, which are not included in requirements.txt:
```
smbus
```

These are mocked using `fake-rpi` if they can't be imported.

On the raspi you'll need `libblas` before installing scipy:
```bash
sudo apt-get install libblas-dev
```

### Configuration

Therm uses a database to store temperature observations and thermostat state.
Any DB that SQLALchemy can talk to works. To configure your DB, set the
following environment variables (or handcode them in `therm.settings` if you're
feeling bold):
```bash

```

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


