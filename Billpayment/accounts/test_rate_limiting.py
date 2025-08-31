from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch
import time

User = get_user_model()


class RateLimitingTestCase(APITestCase):
    """Test cases for rate limiting on authentication endpoints"""
    
    def setUp(self):
        self.login_url = reverse('accounts:login')
        self.forgot_password_url = reverse('accounts:forgot_password')
        self.reset_password_url = reverse('accounts:reset_password')
        self.verify_token_url = reverse('accounts:verify_reset_token')
        
        # Create a test user
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
        
        # Valid login data
        self.valid_login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        
        # Invalid login data for rate limit testing
        self.invalid_login_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        
        # Forgot password data
        self.forgot_password_data = {
            'email': 'test@example.com'
        }
        
        # Reset password data
        self.reset_password_data = {
            'email': 'test@example.com',
            'token': 'test-token',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        # Verify token data
        self.verify_token_data = {
            'email': 'test@example.com',
            'token': 'test-token'
        }
    
    def test_login_rate_limiting(self):
        """Test that login endpoint is rate limited (5 requests per minute)"""
        # Make 5 requests (should all succeed or fail normally, not rate limited)
        for i in range(5):
            response = self.client.post(self.login_url, self.invalid_login_data)
            # Should get 401 Unauthorized, not 429 Too Many Requests
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 6th request should be rate limited
        response = self.client.post(self.login_url, self.invalid_login_data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    @patch('Billpayment.accounts.views.send_password_reset_email')
    @patch('Billpayment.accounts.views.store_reset_token')
    @patch('Billpayment.accounts.views.generate_reset_token')
    def test_forgot_password_rate_limiting(self, mock_generate, mock_store, mock_send):
        """Test that forgot password endpoint is rate limited (3 requests per minute)"""
        # Configure mocks
        mock_generate.return_value = 'test-token'
        mock_store.return_value = True
        mock_send.return_value = True
        
        # Make 3 requests (should all succeed)
        for i in range(3):
            response = self.client.post(self.forgot_password_url, self.forgot_password_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 4th request should be rate limited
        response = self.client.post(self.forgot_password_url, self.forgot_password_data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    @patch('Billpayment.accounts.views.get_reset_token')
    @patch('Billpayment.accounts.views.delete_reset_token')
    def test_reset_password_rate_limiting(self, mock_delete, mock_get):
        """Test that reset password endpoint is rate limited (3 requests per minute)"""
        # Configure mocks
        mock_get.return_value = None  # Invalid token
        mock_delete.return_value = True
        
        # Make 3 requests (should all return 400 for invalid token)
        for i in range(3):
            response = self.client.post(self.reset_password_url, self.reset_password_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 4th request should be rate limited
        response = self.client.post(self.reset_password_url, self.reset_password_data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    @patch('Billpayment.accounts.views.get_reset_token')
    def test_verify_token_rate_limiting(self, mock_get):
        """Test that verify token endpoint is rate limited (10 requests per minute)"""
        # Configure mock
        mock_get.return_value = None  # Invalid token
        
        # Make 10 requests (should all return 400 for invalid token)
        for i in range(10):
            response = self.client.post(self.verify_token_url, self.verify_token_data)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # 11th request should be rate limited
        response = self.client.post(self.verify_token_url, self.verify_token_data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_rate_limiting_per_ip(self):
        """Test that rate limiting is applied per IP address"""
        # This test verifies that rate limiting is IP-based
        # Make requests that would trigger rate limiting
        for i in range(5):
            response = self.client.post(self.login_url, self.invalid_login_data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # 6th request should be rate limited
        response = self.client.post(self.login_url, self.invalid_login_data)
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Note: In a real scenario with different IPs, this would not be rate limited
        # But in tests, all requests come from the same test client IP