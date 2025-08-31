from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import validate_email


class User(AbstractUser):
    """
    Custom User model that uses email as the username field.
    Extends Django's AbstractUser to provide email-based authentication.
    """
    email = models.EmailField(
        unique=True,
        validators=[validate_email],
        help_text='Required. Enter a valid email address.'
    )
    first_name = models.CharField(
        max_length=150,
        help_text='Required. Enter your first name.'
    )
    last_name = models.CharField(
        max_length=150,
        help_text='Required. Enter your last name.'
    )
    is_email_verified = models.BooleanField(
        default=False,
        help_text='Designates whether the user has verified their email address.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Use email as the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        """Return the user's full name."""
        return f"{self.first_name} {self.last_name}".strip()
    
    def save(self, *args, **kwargs):
        """Override save to ensure email is lowercase."""
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)
