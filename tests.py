import unittest

class TestAPI(unittest.TestCase):
    def test_online(self):
        from API import check_online
        check_online()

if __name__ == '__main__':
    unittest.main()
