import unittest

import therm


def test_get_samples(client, temp_data):
    results = client.get("/samples").get_json()
    print(results)
    assert len(results) == len(temp_data)


def test_get_main(client):
    rv = client.get("/")
    assert "Temp: " in rv.data.decode()
