import unittest
from unittest import mock
from requests.exceptions import ConnectionError
import socket
import API
import main

# Utility functions to help with testing
WIFI_ENABLED = True

def stop_wifi():
    global WIFI_ENABLED
    WIFI_ENABLED = False

def start_wifi():
    global WIFI_ENABLED
    WIFI_ENABLED = True

def guarded(*args, **kwargs):
    if not WIFI_ENABLED:
        raise ConnectionError("No internet! Totally!")
    else:
        # SocketType is a valid public alias of socket.socket,
        # we use it here to avoid namespace collisions
        return socket.SocketType(*args, **kwargs)

socket.socket = guarded

# Unit tests
class TestAPI(unittest.TestCase):
    @mock.patch('API.input', create=True)
    def test_cityChooser(self, mocked_input):
        def test(inp, *outs):
            mocked_input.side_effect = [inp]
            res = API.cityChooser()
            self.assertEqual(res, outs)
        
        # Test all inputs and expected outputs
        test('', 'Sydney', 'Australia')
        test('CitynameHere', 'CitynameHere', 'Australia')
        test('City country', 'City', 'country')
        test('a b c d', 'a', 'b c d')
        test('ct,cntree', 'ct', 'cntree')
        test('hi, BYE!', 'hi', 'BYE!')
    
    def test_get_location(self):
        # Ensure it works first
        lat, lon, bbx = API.get_location('Sydney', 'Australia')
        self.assertIsInstance(lat, float)
        self.assertIsInstance(lon, float)
        self.assertIsInstance(bbx, list)
        for it in bbx:
            self.assertIsInstance(it, float)
        lat, lon, bbx = API.get_location('Tokyo', 'Japan')
        self.assertIsInstance(lat, float)
        self.assertIsInstance(lon, float)
        self.assertIsInstance(bbx, list)
        for it in bbx:
            self.assertIsInstance(it, float)

        # Test with bad values
        with self.assertRaises(ValueError):
            API.get_location(123, 'Australia')
        with self.assertRaises(ValueError):
            API.get_location('Sydney', ['Australia'])
        with self.assertRaises(ValueError):
            API.get_location(None, {'a': 1})
        
        # Test with no wifi
        try:
            stop_wifi()
            with self.assertRaises(ConnectionError):
                API.get_location('Sydney', 'Australia')
        finally:
            start_wifi()
        
        # Test places that do not exist
        self.assertEqual(API.get_location('Amshadsplat', 'Australia'), (None, None, None))
        self.assertEqual(API.get_location('Sydney', 'MarkMyWords'), (None, None, None))
        self.assertEqual(API.get_location('This place', 'Does not exist'), (None, None, None))

    def test_lat_lngTOxy(self):
        # Test edges and in bounds
        for lat in range(-90, 91, 60): # [-90, -30, 30, 90]
            for long in range(-180, 181, 90): # [-180, -90, 0, 90, 180]
                for zoom in (0, 8, 16, 23):
                    x, y = API.lat_lngTOxy(lat, long, zoom)
                    self.assertIsInstance(x, int)
                    self.assertIsInstance(y, int)
                    x, y = API.lat_lngTOxy(lat, long, zoom, True)
                    self.assertIsInstance(x, float)
                    self.assertIsInstance(y, float)

        # Test out of bounds
        for lat in (-91, 0, 91):
            for long in (-181, 0, 181):
                if (lat, long) == (0, 0):
                    continue
                for zoom in (-1, 12, 24):
                    x, y = API.lat_lngTOxy(lat, long, zoom)
                    self.assertIs(x, None)
                    self.assertIs(y, None)
                    x, y = API.lat_lngTOxy(lat, long, zoom, True)
                    self.assertIs(x, None)
                    self.assertIs(y, None)
        
        # Test bad inputs
        with self.assertRaises(ValueError):
            API.lat_lngTOxy(None, 3, 9)
        with self.assertRaises(ValueError):
            API.lat_lngTOxy(7, [0], 0)
        with self.assertRaises(ValueError):
            API.lat_lngTOxy(7, 4, 0.5)
        with self.assertRaises(ValueError):
            API.lat_lngTOxy(0, 9, 'a')
        with self.assertRaises(ValueError):
            API.lat_lngTOxy(10, 3, 9, None)

    def _xyzT(self, fun, check):
        # Check in-bounds
        for z in range(0, 14, 4):
            tot = pow(2, z)
            step = max(tot//2, 1)
            for x in range(0, tot, step):
                for y in range(0, tot, step):
                    out = fun(x, y, z)
                    check(out)

        # Check out of bounds
        for z in range(0, 17, 4):
            tot = pow(2, z)
            for x in (-1, tot):
                for y in (-1, tot):
                    with self.assertRaises(ValueError):
                        fun(x, y, z)

        # Check bad values
        with self.assertRaises(ValueError):
            fun(None, 0, 2)
        with self.assertRaises(ValueError):
            fun(0, 'a', 4)
        with self.assertRaises(ValueError):
            fun(5, 12, {'G': 9})

        # Check no wifi
        try:
            stop_wifi()
            with self.assertRaises(ConnectionError):
                fun(0, 0, 2)
        finally:
            start_wifi()
    
    def test_getPlaceInfo(self):
        def check(out):
            self.assertIsInstance(out, list)
            for feat in out:
                self.assertIsInstance(feat, dict)
                self.assertTrue(all(i in feat.keys() for i in (
                    'type',
                    'coords',
                    'importance',
                    'kind',
                    'group',
                    'name'
                )))
        self._xyzT(API.getPlaceInfo, check)

    def test_getHeightInfo(self):
        from pygame import Surface
        def check(out):
            self.assertIsInstance(out, Surface)
        self._xyzT(API.getHeightInfo, check)

    def test_moneyFuncs(self):
        for fun in (API.getPropertyPrice, API.getTotMoney):
            self.assertIsInstance(fun('Australia'), (int, float))
            with self.assertRaises(ValueError):
                fun(123)
            self.assertIs(fun('123'), None)
            try:
                stop_wifi()
                with self.assertRaises(ConnectionError):
                    fun('Australia')
            finally:
                start_wifi()

# Integration / system tests
class TestMain(unittest.TestCase):
    @mock.patch('API.input', create=True)
    @mock.patch('main.input', create=True)
    def test_noWifi(self, mainInp, apiInp):
        apiInp.side_effect = ['']
        mainInp.side_effect = [''] # Press to exit
        try:
            stop_wifi()
            with self.assertRaises(ConnectionError):
                main.main()
        finally:
            start_wifi()

    @mock.patch('API.input', create=True)
    @mock.patch('main.input', create=True)
    def test_badInputs(self, mainInp, apiInp):
        # Places do not exist
        mainInp.side_effect = ['', '', '']

        apiInp.side_effect = ['fub<hjdvyuiw@#$%^&*()_@!@#:"}{hjg']
        with self.assertRaises(ValueError):
            main.main()

        apiInp.side_effect = ['Sydney xerctyybjhgdcxydtgfcgyubhjyg']
        with self.assertRaises(ValueError):
            main.main()

        apiInp.side_effect = ['ayudsbw3ui 3267454']
        with self.assertRaises(ValueError):
            main.main()

if __name__ == '__main__':
    unittest.main()
