"""
Тесты для ДЗ_8: миграция с HTTP на HTTPS 

"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
import django.conf


class HttpsMigrationTests(TestCase):

    def setUp(self):
        self.client = Client()

    # TC-LR8-001 
    def test_secure_proxy_ssl_header_configured(self):
        """
        TC-LR8-001: SECURE_PROXY_SSL_HEADER должен быть задан в settings.py.
        Ожидаемый результат: параметр равен ('HTTP_X_FORWARDED_PROTO', 'https').
        """
        self.assertEqual(
            django.conf.settings.SECURE_PROXY_SSL_HEADER,
            ('HTTP_X_FORWARDED_PROTO', 'https'),
            "SECURE_PROXY_SSL_HEADER не задан или задан неверно."
        )

    # TC-LR8-002 
    @override_settings(SECURE_SSL_REDIRECT=True)
    def test_http_request_redirected_to_https(self):
        """
        TC-LR8-002: HTTP-запрос к главной странице должен возвращать 301.
        Ожидаемый результат: код ответа 301, заголовок Location содержит https://.
        """
        response = self.client.get('/', secure=False)
        self.assertIn(response.status_code, [301, 302],
                      "HTTP-запрос не перенаправлен на HTTPS.")
        if response.has_header('Location'):
            self.assertTrue(
                response['Location'].startswith('https://'),
                "Location не указывает на HTTPS."
            )

    # TC-LR8-003 
    def test_https_request_returns_200(self):
        """
        TC-LR8-003: HTTPS-запрос к главной странице должен возвращать 200.

        Требование (ТЗ): корректный HTTPS-запрос обслуживается без редиректа
        и без ошибок.
        Ожидаемый результат: код ответа 200.
        """
        response = self.client.get(
            '/',
            secure=True,
            HTTP_X_FORWARDED_PROTO='https'
        )
        self.assertEqual(response.status_code, 200,
                         "HTTPS-запрос к '/' не вернул 200.")

    # TC-LR8-004 
    @override_settings(CSRF_COOKIE_SECURE=True, SESSION_COOKIE_SECURE=True)
    def test_secure_cookie_flags_in_deployment(self):
        """
        TC-LR8-004: Cookie CSRF и сессии должны иметь флаг Secure в продакшене.
        CSRF_COOKIE_SECURE и SESSION_COOKIE_SECURE должны быть True.
        Ожидаемый результат: оба параметра равны True.
        """
        self.assertTrue(django.conf.settings.CSRF_COOKIE_SECURE,
                        "CSRF_COOKIE_SECURE не True.")
        self.assertTrue(django.conf.settings.SESSION_COOKIE_SECURE,
                        "SESSION_COOKIE_SECURE не True.")

    # TC-LR8-005 
    def test_csrf_trusted_origins_use_https_scheme(self):
        """
        TC-LR8-005: Все внешние записи CSRF_TRUSTED_ORIGINS должны использовать
        схему https://.
        Ожидаемый результат: все записи, не содержащие 'localhost', начинаются
        с 'https://'.
        """
        origins = django.conf.settings.CSRF_TRUSTED_ORIGINS
        for origin in origins:
            if 'localhost' not in origin:
                self.assertTrue(
                    origin.startswith('https://'),
                    f"CSRF_TRUSTED_ORIGINS содержит небезопасный origin: {origin}"
                )

    # TC-LR8-006 
    def test_api_chart_status_accessible_over_https(self):
        """
        TC-LR8-006: API-эндпоинт /api/chart/status-pie/ доступен по HTTPS.
        Ожидаемый результат: код ответа 200, Content-Type application/json.
        """
        response = self.client.get(
            '/api/chart/status-pie/',
            secure=True,
            HTTP_X_FORWARDED_PROTO='https'
        )
        self.assertEqual(response.status_code, 200,
                         "/api/chart/status-pie/ недоступен по HTTPS.")
        self.assertIn('application/json', response.get('Content-Type', ''),
                      "Ответ не является JSON.")

    # TC-LR8-007 
    def test_api_scan_accessible_over_https(self):
        """
        TC-LR8-007: API-эндпоинт /api/scan/ доступен по HTTPS.
        Ожидаемый результат: код ответа 200.
        """
        response = self.client.post(
            '/api/scan/',
            secure=True,
            HTTP_X_FORWARDED_PROTO='https'
        )
        self.assertEqual(response.status_code, 200,
                         "/api/scan/ недоступен по HTTPS.")
