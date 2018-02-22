import unittest
import gymbot
import gspread
from oauth2client.service_account import ServiceAccountCredentials


class TestGymBot(unittest.TestCase):
    def test_twiliofy(self):
        inner = 'This is a test string'
        outer = gymbot.twiliofy(inner)
        self.assertEqual(outer, '<?xml version=\"1.0\" encoding=\"UTF-8\"?><Response><Message>' + inner + '</Message></Response>')

if __name__ == '__main__':
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('/Users/ajonnav/Downloads/gymbot-sheets-creds.json', scope)
    gc = gspread.authorize(credentials)
    wks = gc.open("Gym Tallies").sheet1
    wks.update_acell('A1', 1)
    unittest.main()
