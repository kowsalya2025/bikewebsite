from django import forms
from django.core.validators import RegexValidator
import re
# from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# from django.contrib.auth.models import User
# from django.core.exceptions import ValidationError
# from .models import UserProfile

class ContactForm(forms.Form):
    REASON_CHOICES = [
        ('', 'Select a reason...'),
        ('general_enquiry', 'General Enquiry'),
        ('buy_bike', 'Buy a Bike'),
        ('sell_bike', 'Sell a Bike'),
        ('exchange_bike', 'Exchange a Bike'),
        ('rto_service', 'RTO Service'),
        ('others', 'Others'),
    ]
    
    SOURCE_CHOICES = [
        ('', 'Select an option...'),
        ('google', 'Google Search'),
        ('social', 'Social Media'),
        ('friend', 'Friend/Family'),
        ('advertisement', 'Advertisement'),
        ('other', 'Other'),
    ]
    
    # Phone number validator
    phone_validator = RegexValidator(
        regex=r'^[\+]?[1-9][\d]{0,15}$',
        message='Enter a valid phone number (e.g., +91 9876543210 or 9876543210)'
    )
    
    name = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        }),
        error_messages={
            'required': 'Name is required.',
            'max_length': 'Name cannot exceed 100 characters.'
        }
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Please enter a valid email address.'
        }
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        }),
        error_messages={
            'max_length': 'Phone number cannot exceed 20 characters.'
        }
    )
    
    reason = forms.ChoiceField(
        choices=REASON_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        error_messages={
            'required': 'Please select a reason for contact.',
            'invalid_choice': 'Please select a valid reason.'
        }
    )
    
    source = forms.ChoiceField(
        choices=SOURCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        error_messages={
            'invalid_choice': 'Please select a valid option.'
        }
    )
    
    message = forms.CharField(
        required=True,
        min_length=10,
        max_length=1000,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Enter your message here...'
        }),
        error_messages={
            'required': 'Message is required.',
            'min_length': 'Message must be at least 10 characters long.',
            'max_length': 'Message cannot exceed 1000 characters.'
        }
    )
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            # Remove extra whitespaces and ensure only letters and spaces
            name = re.sub(r'\s+', ' ', name.strip())
            if not re.match(r'^[a-zA-Z\s]+$', name):
                raise forms.ValidationError('Name should only contain letters and spaces.')
            if len(name) < 2:
                raise forms.ValidationError('Name must be at least 2 characters long.')
        return name
    
    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remove all non-digit characters except +
            cleaned_phone = re.sub(r'[^\d+]', '', phone)
            
            # Basic phone number validation
            if len(cleaned_phone) < 10:
                raise forms.ValidationError('Phone number must be at least 10 digits long.')
            
            if len(cleaned_phone) > 15:
                raise forms.ValidationError('Phone number cannot exceed 15 digits.')
                
            return cleaned_phone
        return phone
    
    def clean_message(self):
        message = self.cleaned_data.get('message')
        if message:
            # Remove extra whitespaces
            message = re.sub(r'\s+', ' ', message.strip())
            
            # Check for spam-like content (basic check)
            spam_words = ['viagra', 'casino', 'lottery', 'winner', 'click here']
            message_lower = message.lower()
            
            for word in spam_words:
                if word in message_lower:
                    raise forms.ValidationError('Message contains inappropriate content.')
            
        return message
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Additional validation if needed
        name = cleaned_data.get('name')
        email = cleaned_data.get('email')
        message = cleaned_data.get('message')
        
        # Check if name and email are too similar (possible spam)
        if name and email and name.lower().replace(' ', '') in email.lower():
            # This is just a warning, not an error
            pass
            
        return cleaned_data
    

from .models import Motorcycle

class MotorcycleForm(forms.ModelForm):
    class Meta:
        model = Motorcycle
        fields = ['brand', 'model', 'variant', 'year', 'kms_driven', 'owner']