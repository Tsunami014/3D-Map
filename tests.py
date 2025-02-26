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

if __name__ == '__main__':
    unittest.main()
