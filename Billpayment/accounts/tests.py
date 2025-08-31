from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
import json

User = get_user_model()


class UserRegistrationTestCase(APITestCase):
    """Test cases for user registration endpoint"""
    
    def setUp(self):
        self.registration_url = reverse('accounts:register')
        self.valid_user_data = {
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
        }
    
    def test_successful_user_registration(self):
        """Test successful user registration with valid data"""
        response = self.client.post(self.registration_url, self.valid_user_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)
        
        # Verify user was created in database
        user = User.objects.get(email='test@example.com')
        self.assertEqual(user.first_name, 'Test')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.check_password('TestPassword123!'))
    
    def test_registration_with_existing_email(self):
        """Test registration fails with existing email"""
        # Create user first
        User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='password123'
        )
        
        response = self.client.post(self.registration_url, self.valid_user_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_registration_with_invalid_email(self):
        """Test registration fails with invalid email format"""
        invalid_data = self.valid_user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post(self.registration_url, invalid_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)
    
    def test_registration_with_weak_password(self):
        """Test registration fails with weak password"""
        weak_data = self.valid_user_data.copy()
        weak_data['password'] = '123'
        weak_data['password_confirm'] = '123'
        
        response = self.client.post(self.registration_url, weak_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
    
    def test_registration_with_mismatched_passwords(self):
        """Test registration fails when passwords don't match"""
        mismatch_data = self.valid_user_data.copy()
        mismatch_data['password_confirm'] = 'DifferentPassword123!'
        
        response = self.client.post(self.registration_url, mismatch_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password_confirm', response.data)
    
    def test_registration_with_missing_fields(self):
        """Test registration fails with missing required fields"""
        incomplete_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
            # Missing first_name, last_name, password_confirm
        }
        
        response = self.client.post(self.registration_url, incomplete_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('first_name', response.data)
        self.assertIn('last_name', response.data)
        self.assertIn('password_confirm', response.data)


class UserLoginTestCase(APITestCase):
    """Test cases for user login endpoint"""
    
    def setUp(self):
        self.login_url = reverse('accounts:login')
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
    
    def test_successful_login(self):
        """Test successful login with valid credentials"""
        login_data = {
            'email': 'test@example.com',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('access', response.data['tokens'])
        self.assertIn('refresh', response.data['tokens'])
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], 'test@example.com')
    
    def test_login_with_invalid_email(self):
        """Test login fails with non-existent email"""
        login_data = {
            'email': 'nonexistent@example.com',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_with_invalid_password(self):
        """Test login fails with incorrect password"""
        login_data = {
            'email': 'test@example.com',
            'password': 'WrongPassword123!'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
    
    def test_login_with_missing_fields(self):
        """Test login fails with missing required fields"""
        incomplete_data = {
            'email': 'test@example.com'
            # Missing password
        }
        
        response = self.client.post(self.login_url, incomplete_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetTestCase(APITestCase):
    """Test cases for password reset endpoints"""
    
    def setUp(self):
        self.forgot_password_url = reverse('accounts:forgot_password')
        self.reset_password_url = reverse('accounts:reset_password')
        self.verify_token_url = reverse('accounts:verify_reset_token')
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
    
    @patch('Billpayment.accounts.views.send_password_reset_email')
    @patch('Billpayment.accounts.views.store_reset_token')
    @patch('Billpayment.accounts.views.generate_reset_token')
    def test_forgot_password_success(self, mock_generate, mock_store, mock_send):
        """Test successful forgot password request"""
        mock_generate.return_value = 'test-token-123'
        mock_store.return_value = True
        mock_send.return_value = True
        
        data = {'email': 'test@example.com'}
        response = self.client.post(self.forgot_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        mock_generate.assert_called_once()
        mock_store.assert_called_once()
        mock_send.assert_called_once()
    
    def test_forgot_password_nonexistent_email(self):
        """Test forgot password with non-existent email (should still return success for security)"""
        data = {'email': 'nonexistent@example.com'}
        response = self.client.post(self.forgot_password_url, data)
        
        # Should return success to prevent email enumeration
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
    
    @patch('Billpayment.accounts.views.get_reset_token')
    @patch('Billpayment.accounts.views.delete_reset_token')
    def test_reset_password_success(self, mock_delete, mock_get):
        """Test successful password reset with valid token"""
        # Mock get_reset_token to return the same token we're sending
        def mock_get_token(email):
            if email == 'test@example.com':
                return 'valid-token-123'
            return None
        mock_get.side_effect = mock_get_token
        mock_delete.return_value = True
        
        data = {
            'email': 'test@example.com',
            'token': 'valid-token-123',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        response = self.client.post(self.reset_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))
    
    @patch('Billpayment.accounts.views.get_reset_token')
    def test_reset_password_invalid_token(self, mock_get):
        """Test password reset fails with invalid token"""
        mock_get.return_value = None
        
        data = {
            'email': 'test@example.com',
            'token': 'invalid-token',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        response = self.client.post(self.reset_password_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    @patch('Billpayment.accounts.views.get_reset_token')
    def test_verify_reset_token_valid(self, mock_get):
        """Test verify reset token with valid token"""
        def mock_get_token(email):
            if email == 'test@example.com':
                return 'valid-token-123'
            return None
        mock_get.side_effect = mock_get_token
        
        data = {
            'email': 'test@example.com',
            'token': 'valid-token-123'
        }
        
        response = self.client.post(self.verify_token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('valid', response.data)
        self.assertTrue(response.data['valid'])
    
    @patch('Billpayment.accounts.views.get_reset_token')
    def test_verify_reset_token_invalid(self, mock_get):
        """Test token verification with invalid token"""
        mock_get.return_value = None
        
        data = {
            'email': 'test@example.com',
            'token': 'invalid-token'
        }
        
        response = self.client.post(self.verify_token_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('valid', response.data)
        self.assertFalse(response.data['valid'])


class UserProfileTestCase(APITestCase):
    """Test cases for user profile endpoint"""
    
    def setUp(self):
        self.profile_url = reverse('accounts:profile')
        self.user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='TestPassword123!',
            first_name='Test',
            last_name='User'
        )
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
    
    def test_get_user_profile_authenticated(self):
        """Test getting user profile when authenticated"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['first_name'], 'Test')
        self.assertEqual(response.data['last_name'], 'User')
    
    def test_get_user_profile_unauthenticated(self):
        """Test getting user profile when not authenticated"""
        response = self.client.get(self.profile_url)
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_update_user_profile(self):
        """Test updating user profile"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        
        update_data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        response = self.client.patch(self.profile_url, update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['first_name'], 'Updated')
        self.assertEqual(response.data['last_name'], 'Name')
        
        # Verify changes in database
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Updated')
        self.assertEqual(self.user.last_name, 'Name')
