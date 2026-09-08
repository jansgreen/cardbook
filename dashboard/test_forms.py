from django import forms
from django.test import SimpleTestCase

from dashboard.forms import normalize_whatsapp_url


class WhatsAppUrlNormalizationTests(SimpleTestCase):
    def test_accepts_wa_me_url(self):
        self.assertEqual(normalize_whatsapp_url("https://wa.me/19172135087"), "https://wa.me/19172135087")

    def test_accepts_plain_phone_number(self):
        self.assertEqual(normalize_whatsapp_url("+1 (917) 213-5087"), "https://wa.me/19172135087")

    def test_rejects_non_whatsapp_domain(self):
        with self.assertRaises(forms.ValidationError):
            normalize_whatsapp_url("https://example.com/19172135087")
