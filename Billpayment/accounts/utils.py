import redis
import secrets
import string
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags


# Redis connection
try:
    redis_client = redis.Redis(
        host=getattr(settings, 'REDIS_HOST', 'localhost'),
        port=getattr(settings, 'REDIS_PORT', 6379),
        db=getattr(settings, 'REDIS_DB', 0),
        decode_responses=True
    )
except Exception:
    # Fallback to in-memory storage for development
    redis_client = None
    _memory_store = {}


def generate_reset_token(length=32):
    """Generate a secure random token for password reset"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def store_reset_token(email, token, expiry_seconds=3600):
    """Store password reset token in Redis with expiry"""
    key = f"password_reset:{email.lower()}"
    
    if redis_client:
        try:
            redis_client.setex(key, expiry_seconds, token)
            return True
        except Exception:
            pass
    
    # Fallback to memory storage for development
    global _memory_store
    _memory_store[key] = token
    return True


def get_reset_token(email):
    """Retrieve password reset token from Redis"""
    key = f"password_reset:{email.lower()}"
    
    if redis_client:
        try:
            return redis_client.get(key)
        except Exception:
            pass
    
    # Fallback to memory storage
    global _memory_store
    return _memory_store.get(key)


def delete_reset_token(email):
    """Delete password reset token from Redis"""
    key = f"password_reset:{email.lower()}"
    
    if redis_client:
        try:
            redis_client.delete(key)
            return True
        except Exception:
            pass
    
    # Fallback to memory storage
    global _memory_store
    if key in _memory_store:
        del _memory_store[key]
    return True


def send_password_reset_email(user, reset_token, request=None):
    """Send password reset email to user"""
    try:
        # Get the domain from request or use default
        domain = request.get_host() if request else 'localhost:8000'
        protocol = 'https' if request and request.is_secure() else 'http'
        
        # Create reset URL (you can customize this based on your frontend)
        reset_url = f"{protocol}://{domain}/reset-password?token={reset_token}&email={user.email}"
        
        # Email context
        context = {
            'user': user,
            'reset_url': reset_url,
            'reset_token': reset_token,
            'domain': domain,
        }
        
        # Render email content
        subject = 'Password Reset Request'
        html_message = f"""
        <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Hello {user.first_name},</p>
            <p>You have requested to reset your password. Click the link below to reset your password:</p>
            <p><a href="{reset_url}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Reset Password</a></p>
            <p>Or copy and paste this link in your browser:</p>
            <p>{reset_url}</p>
            <p>This link will expire in 1 hour.</p>
            <p>If you did not request this password reset, please ignore this email.</p>
            <br>
            <p>Best regards,<br>The Bill Payment Team</p>
        </body>
        </html>
        """
        
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@billpayment.com',
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False