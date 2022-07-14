from django.urls import reverse
import unittest
from rest_framework.test import APITestCase, APIClient


class DepositTestCase(APITestCase):
    def setUp(self):
        pass

    def test_valid_deposit(self):
        deposit_request = {'username': 'muda',
                           'key': '8d546f77-56fa-4273-ac74-eef8364eb813',
                           'deposit': 50}
        # login_url = reverse('login')
        deposit_url = reverse('deposit')

        response = self.client.put(deposit_url, deposit_request)
        resp = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp['status'], "User deposit updated successful")


class BuyTestCase(APITestCase):
    def setUp(self):
        pass

    def test_valid_deposit(self):
        deposit_request = {'username': 'muda',
                           'key': '8d546f77-56fa-4273-ac74-eef8364eb813',
                           'product_id': 12,
                           'product_amount': 1}
        buy_url = reverse('buy')

        response = self.client.put(buy_url, deposit_request)
        resp = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(resp['change'], 30)

#
# if __name__ == '__main__':
#     unittest.main()
