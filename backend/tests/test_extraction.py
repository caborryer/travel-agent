import unittest

from app.agent.nodes import (
    _destination_matches_text,
    _extract_destination_regex,
    _is_grounded_in_sources,
    _parse_price,
    _price_appears_in_text,
    _sanitize_destination,
)


class TestDestinationExtraction(unittest.TestCase):
    def test_cancun_con_presupuesto(self):
        msg = "QUIERO IR A CANCUN CON UN PRESUPUESTO DE 1000 USD"
        self.assertEqual(_extract_destination_regex(msg), "Cancun")

    def test_viajar_madrid_con_euros(self):
        msg = "viajar a Madrid con 500 euros"
        self.assertEqual(_extract_destination_regex(msg), "Madrid")

    def test_sanitize_strips_prepositions(self):
        self.assertEqual(_sanitize_destination("CANCUN CON"), "Cancun")
        self.assertEqual(_sanitize_destination("Madrid de"), "Madrid")

    def test_destination_matches_primary_token(self):
        text = "Cheap flights to Cancún from NYC"
        self.assertTrue(_destination_matches_text(text, "Cancun"))

    def test_parse_european_thousands(self):
        value, currency = _parse_price("4.950€")
        self.assertEqual(value, 4950.0)
        self.assertEqual(currency, "EUR")

    def test_parse_european_decimal(self):
        value, _ = _parse_price("585,00 €")
        self.assertEqual(value, 585.0)

    def test_price_appears_in_snippet(self):
        snippet = "Viaje a Cancun desde 800 USD por persona"
        self.assertTrue(_price_appears_in_text("800 USD", snippet))
        self.assertFalse(_price_appears_in_text("999 USD", snippet))

    def test_grounding_rejects_invented_price(self):
        search_results = [
            {
                "url": "https://example.com/cancun",
                "title": "Cancun deals",
                "content": "Trips to Cancun from 800 USD",
            }
        ]
        grounded = {
            "name": "Cancun",
            "estimated_price": "800 USD",
            "source": "https://example.com/cancun",
        }
        fake = {
            "name": "Cancun",
            "estimated_price": "50 USD",
            "source": "https://example.com/cancun",
        }
        allowed = {"https://example.com/cancun"}
        self.assertTrue(_is_grounded_in_sources(grounded, search_results, [], allowed))
        self.assertFalse(_is_grounded_in_sources(fake, search_results, [], allowed))

    def test_grounding_rejects_unknown_url(self):
        dest = {
            "name": "Cancun",
            "estimated_price": "800 USD",
            "source": "https://fake.com/trip",
        }
        search_results = [
            {"url": "https://example.com/cancun", "title": "Cancun", "content": "800 USD"},
        ]
        self.assertFalse(
            _is_grounded_in_sources(dest, search_results, [], {"https://example.com/cancun"})
        )


if __name__ == "__main__":
    unittest.main()
