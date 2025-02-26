import unittest

class TestAPI(unittest.TestCase):
    def test_online(self):
        from API import check_online
        check_online()
    
    def test_locations(self):
        from API import get_location
        for loc in ['Sydney', 'Melborne', 'Newcastle']:
            lat, long = get_location(loc)
            self.assertIsInstance(lat, float)
            self.assertIsInstance(long, float)
    
    def test_planetData(self):
        from API import planetDataPth, planetDataFile
        for place in ['', 'asia/']:
            obj = planetDataPth(place)
            self.assertIsInstance(obj, list)
            for i in obj:
                self.assertIsInstance(i, str)
        self.assertIsInstance(planetDataFile('europe.poly'), str)

if __name__ == '__main__':
    unittest.main()
