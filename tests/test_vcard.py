import unittest
from pythonvCard4.vcard import Contact, ValidationError
from datetime import date

class TestContact(unittest.TestCase):
    def test_round_trip(self):
        c = Contact(
            fn="Alice",
            email=[ {"value":"alice@example.com", "type":["work"]} ],
            tel=[ {"value":"+1234567890","type":["cell"]} ],
            bday=date(1990,1,1)
        )
        text = c.to_vcard()
        parsed = Contact.from_vcard(text)
        self.assertEqual(parsed.fn, "Alice")
        self.assertEqual(parsed.email[0]["value"], "alice@example.com")
        self.assertEqual(parsed.bday, date(1990,1,1))

    def test_missing_fn(self):
        with self.assertRaises(ValidationError):
            Contact(fn="").to_vcard()

if __name__ == '__main__':
    unittest.main()
