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



