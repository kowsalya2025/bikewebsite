from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone
import uuid
# from django.contrib.auth.models import User
# from django.core.validators import FileExtensionValidator
import os
from django.core.validators import MinValueValidator, MaxValueValidator
from datetime import datetime

# Keep your existing model for carousel
class Bike(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to="bikes/", blank=True, null=True)

    def __str__(self):
        return self.name
    
class FeatureSection(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='features/', blank=True, null=True)

    def __str__(self):
        return self.title


# Add new model for detailed bike listings
class BikeForSale(models.Model):
    FUEL_CHOICES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
    ]
    
    OWNER_CHOICES = [
        ('1st', '1st Owner'),
        ('2nd', '2nd Owner'),
        ('3rd', '3rd Owner'),
    ]
    
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    cc = models.CharField(max_length=10)
    model_variant = models.CharField(max_length=100, blank=True)
    
    year = models.PositiveIntegerField(
          validators=[
        MinValueValidator(1900),
        MaxValueValidator(datetime.now().year + 1)
    ]
    )
    kilometers = models.PositiveIntegerField()
    fuel_type = models.CharField(max_length=20, choices=FUEL_CHOICES)
    owner_number = models.CharField(max_length=10, choices=OWNER_CHOICES)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=100)
    
    image = models.ImageField(upload_to='bikes_for_sale/', blank=True, null=True)
    
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    
    def __str__(self):
        return f"{self.year} | {self.brand} {self.name} | {self.cc}"

    def formatted_price(self):
        return f"₹ {self.price:,.0f}"
    
    def formatted_km(self):
        return f"{self.kilometers:,} Km"




class ContactSubmission(models.Model):
    REASON_CHOICES = [
        ('general_enquiry', 'General Enquiry'),
        ('buy_bike', 'Buy a Bike'),
        ('sell_bike', 'Sell a Bike'),
        ('exchange_bike', 'Exchange a Bike'),
        ('rto_service', 'RTO Service'),
        ('others', 'Others'),
    ]
    
    SOURCE_CHOICES = [
        ('google', 'Google Search'),
        ('social', 'Social Media'),
        ('friend', 'Friend/Family'),
        ('advertisement', 'Advertisement'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Contact information
    name = models.CharField(max_length=100, help_text="Full name of the contact person")
    email = models.EmailField(help_text="Email address for correspondence")
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[RegexValidator(
            regex=r'^[\+]?[1-9][\d]{0,15}$',
            message='Enter a valid phone number'
        )],
        help_text="Optional phone number"
    )
    
    # Form data
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        help_text="Reason for contact"
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        blank=True,
        null=True,
        help_text="How they found out about us"
    )
    message = models.TextField(
        max_length=1000,
        help_text="The message content"
    )
    
    # Metadata
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Status tracking
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        help_text="Current status of the inquiry"
    )
    assigned_to = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_contacts',
        help_text="Staff member assigned to handle this inquiry"
    )
    
    # Admin notes
    admin_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Internal notes for staff"
    )
    
    # Email tracking
    email_sent = models.BooleanField(
        default=False,
        help_text="Whether confirmation email was sent"
    )
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Contact Submission"
        verbose_name_plural = "Contact Submissions"
        db_table = 'contact_submissions'
        
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['reason']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.get_reason_display()} ({self.created_at.strftime('%Y-%m-%d')})"
    
    def save(self, *args, **kwargs):
        # Automatically update the updated_at field
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
    
    @property
    def is_recent(self):
        """Check if the submission is within the last 24 hours"""
        return (timezone.now() - self.created_at).days < 1
    
    @property
    def days_old(self):
        """Calculate how many days old the submission is"""
        return (timezone.now() - self.created_at).days
    
    def get_absolute_url(self):
        """Get the URL for this submission in admin"""
        return f"/admin/yourapp/contactsubmission/{self.id}/change/"
    
    def mark_as_resolved(self, user=None):
        """Mark the submission as resolved"""
        self.status = 'resolved'
        if user:
            self.assigned_to = user
        self.save()
    
    def assign_to_user(self, user):
        """Assign the submission to a user"""
        self.assigned_to = user
        if self.status == 'new':
            self.status = 'in_progress'
        self.save()


class ContactEmailTemplate(models.Model):
    """Model for storing email templates for contact responses"""
    
    TEMPLATE_TYPES = [
        ('confirmation', 'Confirmation Email'),
        ('admin_notification', 'Admin Notification'),
        ('follow_up', 'Follow-up Email'),
        ('resolution', 'Resolution Email'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    subject = models.CharField(max_length=200)
    body_html = models.TextField(help_text="HTML version of the email")
    body_text = models.TextField(help_text="Plain text version of the email")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['template_type', 'name']
        verbose_name = "Email Template"
        verbose_name_plural = "Email Templates"
    
    def __str__(self):
        return f"{self.get_template_type_display()} - {self.name}"


class ContactStatistics(models.Model):
    """Model for storing contact form statistics"""
    
    date = models.DateField(unique=True)
    total_submissions = models.IntegerField(default=0)
    by_reason = models.JSONField(default=dict)  # {"general": 5, "support": 3, etc.}
    by_source = models.JSONField(default=dict)  # {"google": 4, "social": 2, etc.}
    response_rate = models.FloatField(default=0.0)


# login image
class AuthImage(models.Model):
    """Images for login/register page (cake/pastry pictures)."""
    title = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to="auth_images/")
    is_for_login = models.BooleanField(default=False, help_text="Check if this image is for login form")
    is_for_register = models.BooleanField(default=False, help_text="Check if this image is for register form")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title if self.title else f"Image {self.id}"


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    message = models.TextField()
    image = models.ImageField(upload_to='testimonials/')  # saves images in MEDIA/testimonials/

    def __str__(self):
        return self.name
    
class RiderTrustSection(models.Model):
    title = models.CharField(max_length=200, default="Trusted by Riders Like You")
    description = models.TextField()
    image = models.ImageField(upload_to="riders/")

    def __str__(self):
        return self.title


class AboutSection(models.Model):
    title = models.CharField(max_length=200, default="About Us")
    description = models.TextField()
    image = models.ImageField(upload_to="about/")

    def __str__(self):
        return self.title

class MissionSection(models.Model):
    title = models.CharField(max_length=100, default="Our Mission")
    description = models.TextField()
    background_image = models.ImageField(upload_to="about/mission/")

    def __str__(self):
        return self.title
    
class ApproachSection(models.Model):
    title = models.CharField(max_length=200, default="Our Approach")
    description = models.TextField()

    def __str__(self):
        return self.title   


class ApproachImage(models.Model):
    approach = models.ForeignKey(ApproachSection, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="approach_images/")

    def __str__(self):
        return f"Image for {self.approach.title}"



OWNER_CHOICES = [
    ('1st Owner', '1st Owner'),
    ('2nd Owner', '2nd Owner'),
    ('3rd Owner', '3rd Owner'),
    ('4th Owner', '4th Owner'),
    ('5+ Owner', '5+ Owner'),
]

class Motorcycle(models.Model):
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    variant = models.CharField(max_length=100)
    year = models.PositiveIntegerField()
    kms_driven = models.PositiveIntegerField()
    owner = models.CharField(max_length=20, choices=OWNER_CHOICES)
    estimated_price = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.brand} {self.model} ({self.year})"


