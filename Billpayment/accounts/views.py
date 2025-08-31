from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
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


class UserRegistrationView(generics.CreateAPIView):
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
            return Response({
                'message': 'User registered successfully',
                'user': user_serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(access_token)
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """API endpoint for user profile management"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def login_view(request):
    """API endpoint for user login"""
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'error': 'Email and password are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Authenticate user
    user = authenticate(request, username=email.lower(), password=password)
    
    if user is not None:
        if user.is_active:
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Return user data with tokens
            user_serializer = UserSerializer(user)
            return Response({
                'message': 'Login successful',
                'user': user_serializer.data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(access_token)
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'Account is disabled'
            }, status=status.HTTP_401_UNAUTHORIZED)
    else:
        return Response({
            'error': 'Invalid email or password'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """API endpoint for user logout"""
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Invalid token'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def forgot_password_view(request):
    """API endpoint for forgot password request"""
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
                return Response({
                    'message': 'Password reset email sent successfully. Please check your email.'
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    'error': 'Failed to send password reset email. Please try again later.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except User.DoesNotExist:
            # Return success message even if user doesn't exist (security)
            pass
        
        # Always return success message for security
        return Response({
            'message': 'If an account with this email exists, a password reset email has been sent.'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='3/m', method='POST', block=True)
def reset_password_view(request):
    """API endpoint for password reset"""
    serializer = ResetPasswordSerializer(data=request.data)
    
    if serializer.is_valid():
        email = serializer.validated_data['email']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']
        
        # Verify token
        stored_token = get_reset_token(email)
        
        if not stored_token or stored_token != token:
            return Response({
                'error': 'Invalid or expired reset token'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Delete the used token
            delete_reset_token(email)
            
            return Response({
                'message': 'Password reset successful. You can now login with your new password.'
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                'error': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
def verify_reset_token_view(request):
    """API endpoint to verify if reset token is valid"""
    email = request.data.get('email')
    token = request.data.get('token')
    
    if not email or not token:
        return Response({
            'error': 'Email and token are required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Verify token
    stored_token = get_reset_token(email.lower())
    
    if stored_token and stored_token == token:
        return Response({
            'valid': True,
            'message': 'Token is valid'
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'valid': False,
            'message': 'Invalid or expired token'
        }, status=status.HTTP_400_BAD_REQUEST)
