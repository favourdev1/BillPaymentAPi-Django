from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.views.decorators.cache import cache_page
from .models import User
from .serializers import (
    UserRegistrationSerializer, 
    UserSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)
from .utils import (
    generate_reset_token,
    store_reset_token,
    get_reset_token,
    delete_reset_token,
    send_password_reset_email
)
from .mixins import StandardResponseMixin


class UserRegistrationView(StandardResponseMixin, generics.CreateAPIView):
    """API endpoint for user registration"""
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate JWT tokens for the new user
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Return user data with tokens
            user_serializer = UserSerializer(user)
            return self.success_response(
                message='User registered successfully',
                data={
                    'user': user_serializer.data,
                    'tokens': {
                        'refresh': str(refresh),
                        'access': str(access_token)
                    }
                },
                status_code=status.HTTP_201_CREATED
            )
        
        return self.handle_serializer_errors(serializer)


class UserProfileView(StandardResponseMixin, generics.RetrieveUpdateAPIView):
    """API endpoint for user profile management"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        """Get user profile"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return self.success_response(
            message="Profile retrieved successfully",
            data={'user': serializer.data}
        )
    
    def update(self, request, *args, **kwargs):
        """Update user profile"""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        
        if serializer.is_valid():
            self.perform_update(serializer)
            return self.success_response(
                message="Profile updated successfully",
                data={'user': serializer.data}
            )
        
        return self.handle_serializer_errors(serializer)


class LoginView(StandardResponseMixin, APIView):
    """API endpoint for user login"""
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='5/m', method='POST', block=True))
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
             return self.error_response(
                 message='Email and password are required',
                 status_code=status.HTTP_400_BAD_REQUEST
             )
        
        # Authenticate user
        user = authenticate(request, username=email.lower(), password=password)
        
        if user is not None:
            if user.is_active:
                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = refresh.access_token
                
                # Return user data with tokens
                user_serializer = UserSerializer(user)
                return self.success_response(
                    message='Login successful',
                    data={
                        'user': user_serializer.data,
                        'tokens': {
                            'refresh': str(refresh),
                            'access': str(access_token)
                        }
                    }
                )
            else:
                return self.error_response(
                    message='Account is disabled',
                    status_code=status.HTTP_401_UNAUTHORIZED
                )
        else:
            return self.error_response(
                message='Invalid email or password',
                status_code=status.HTTP_401_UNAUTHORIZED
            )


# Keep the function-based view for backward compatibility
@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    """API endpoint for user login (function-based view for backward compatibility)"""
    login_view_instance = LoginView()
    login_view_instance.request = request
    return login_view_instance.post(request)


class LogoutView(StandardResponseMixin, APIView):
    """API endpoint for user logout"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return self.success_response(
                    message='Logout successful'
                )
            else:
                return self.error_response(
                    message='Refresh token is required',
                    status_code=status.HTTP_400_BAD_REQUEST
                )
        except Exception as e:
            return self.error_response(
                message='Invalid refresh token',
                status_code=status.HTTP_400_BAD_REQUEST
            )


# Keep the function-based view for backward compatibility
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """API endpoint for user logout (function-based view for backward compatibility)"""
    logout_view_instance = LogoutView()
    logout_view_instance.request = request
    return logout_view_instance.post(request)


class ForgotPasswordView(StandardResponseMixin, APIView):
    """API endpoint for forgot password"""
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST', block=True))
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = User.objects.get(email=email, is_active=True)
                
                # Generate reset token
                reset_token = generate_reset_token()
                
                # Store token in Redis with 1 hour expiry
                store_reset_token(email, reset_token, expiry_seconds=3600)
                
                # Send password reset email
                email_sent = send_password_reset_email(user, reset_token, request)
                
                if email_sent:
                    return self.success_response(
                        message='Password reset email sent successfully. Please check your email.'
                    )
                else:
                    return self.error_response(
                        message='Failed to send password reset email',
                        errors=['Please try again later'],
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                    
            except User.DoesNotExist:
                # Return success message even if user doesn't exist (security)
                pass
            
            # Always return success message for security
            return self.success_response(
                message='If an account with this email exists, a password reset email has been sent.'
            )
        
        return self.handle_serializer_errors(serializer)


# Keep the function-based view for backward compatibility
@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def forgot_password_view(request):
    """API endpoint for forgot password request (function-based view for backward compatibility)"""
    forgot_password_view_instance = ForgotPasswordView()
    forgot_password_view_instance.request = request
    return forgot_password_view_instance.post(request)


class ResetPasswordView(StandardResponseMixin, APIView):
    """API endpoint for password reset"""
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='3/m', method='POST', block=True))
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        
        if serializer.is_valid():
            email = serializer.validated_data['email']
            token = serializer.validated_data['token']
            new_password = serializer.validated_data['new_password']
            
            # Verify token
            stored_token = get_reset_token(email)
            
            if not stored_token or stored_token != token:
                return self.error_response(
                    message='Password reset failed',
                    errors=['Invalid or expired reset token'],
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user = User.objects.get(email=email, is_active=True)
                
                # Update password
                user.set_password(new_password)
                user.save()
                
                # Delete the used token
                delete_reset_token(email)
                
                return self.success_response(
                    message='Password reset successful. You can now login with your new password.'
                )
                
            except User.DoesNotExist:
                return self.error_response(
                    message='Password reset failed',
                    errors=['User not found'],
                    status_code=status.HTTP_404_NOT_FOUND
                )
        
        return self.handle_serializer_errors(serializer)


# Keep the function-based view for backward compatibility
@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def reset_password_view(request):
    """API endpoint for password reset (function-based view for backward compatibility)"""
    reset_password_view_instance = ResetPasswordView()
    reset_password_view_instance.request = request
    return reset_password_view_instance.post(request)


class VerifyResetTokenView(StandardResponseMixin, APIView):
    """API endpoint to verify if reset token is valid"""
    permission_classes = [AllowAny]
    
    @method_decorator(ratelimit(key='ip', rate='10/m', method='POST', block=True))
    def post(self, request):
        email = request.data.get('email')
        token = request.data.get('token')
        
        if not email or not token:
            return self.error_response(
                message='Token verification failed',
                errors=['Email and token are required'],
                status_code=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify token
        stored_token = get_reset_token(email.lower())
        
        if stored_token and stored_token == token:
            return self.success_response(
                message='Token is valid',
                data={'valid': True}
            )
        else:
            return self.error_response(
                message='Token verification failed',
                errors=['Invalid or expired token'],
                status_code=status.HTTP_400_BAD_REQUEST
            )


# Keep the function-based view for backward compatibility
@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def verify_reset_token_view(request):
    """API endpoint to verify if reset token is valid (function-based view for backward compatibility)"""
    verify_reset_token_view_instance = VerifyResetTokenView()
    verify_reset_token_view_instance.request = request
    return verify_reset_token_view_instance.post(request)
