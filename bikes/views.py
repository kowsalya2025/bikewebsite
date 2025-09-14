from django.shortcuts import render, redirect, get_object_or_404
from .models import Bike, FeatureSection, BikeForSale, Testimonial, RiderTrustSection, AboutSection,MissionSection, ApproachSection
# from django.contrib.auth import login, authenticate, logout
# from django.contrib.auth.decorators import login_required
from django.contrib import messages
# from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
# from django.core.paginator import Paginator
import json
from .models import AuthImage


def home(request):
    bikes = Bike.objects.all()[:5]
    bikes_for_sale = BikeForSale.objects.filter(is_featured=True, is_active=True)[:3]
    feature = FeatureSection.objects.first()
    testimonials = Testimonial.objects.all()[:3]
    rider_section = RiderTrustSection.objects.first()  # ✅ fetch section

    context = {
        'bikes': bikes,
        'bikes_for_sale': bikes_for_sale,
        'feature': feature,
        'testimonials': testimonials,
        'rider_section': rider_section,
    }
    return render(request, "home.html", context)


def search(request):
    query = request.GET.get("q", "")
    results = Bike.objects.filter(name__icontains=query) if query else []
    return render(request, "search.html", {"results": results, "query": query})

# about page
def about(request):
    about_section = AboutSection.objects.first()          # Get about section
    mission = MissionSection.objects.first()              # Get mission section
    approach_section = ApproachSection.objects.prefetch_related("images").first()  # Get approach section + related images

    return render(
        request,
        "about.html",
        {
            "about_section": about_section,
            "mission": mission,
            "approach_section": approach_section,
        }
    )


from django.shortcuts import render
from .models import BikeForSale

def buy_bike(request):
    bikes = BikeForSale.objects.filter(is_active=True)

    # Filters
    brand = request.GET.get("brand")
    year = request.GET.get("year")
    fuel = request.GET.get("fuel_type")
    owner = request.GET.get("owner_number")
    cc = request.GET.get("cc")
    min_price = request.GET.get("min_price")
    max_price = request.GET.get("max_price")
    min_km = request.GET.get("min_km")
    max_km = request.GET.get("max_km")

    if brand:
        bikes = bikes.filter(brand__iexact=brand)
    if year:
        bikes = bikes.filter(year=year)
    if fuel:
        bikes = bikes.filter(fuel_type=fuel)
    if owner:
        bikes = bikes.filter(owner_number=owner)
    if cc:
        bikes = bikes.filter(cc__icontains=cc)
    if min_price:
        bikes = bikes.filter(price__gte=min_price)
    if max_price:
        bikes = bikes.filter(price__lte=max_price)
    if min_km:
        bikes = bikes.filter(kilometers__gte=min_km)
    if max_km:
        bikes = bikes.filter(kilometers__lte=max_km)

    # Sorting
    sort_by = request.GET.get("sort", "newest")
    if sort_by == "price_low":
        bikes = bikes.order_by("price")
    elif sort_by == "price_high":
        bikes = bikes.order_by("-price")
    else:  # newest
        bikes = bikes.order_by("-created_at")

    context = {
        "bikes": bikes,
        "brands": BikeForSale.objects.values_list("brand", flat=True).distinct(),
        "years": BikeForSale.objects.values_list("year", flat=True).distinct(),
    }
    return render(request, "buy_bike.html", context)

def bike_detail(request, id):
    bike = get_object_or_404(BikeForSale, id=id)  # Use the model, not 'bikes'
    return render(request, 'bike_detail.html', {'bike': bike})



from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import never_cache
from django.utils.html import strip_tags
from django.utils import timezone
from django.urls import reverse
import logging
import json
from .forms import ContactForm
from .models import ContactSubmission

# Set up logging
logger = logging.getLogger(__name__)

@csrf_protect
@never_cache
@require_http_methods(["GET", "POST"])
def contact_view(request):
    """
    Handle contact form display and submission for Drive RP
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        
        if form.is_valid():
            try:
                # Get client information
                client_ip = get_client_ip(request)
                user_agent = request.META.get('HTTP_USER_AGENT', '')
                
                # Save to database
                contact_submission = ContactSubmission.objects.create(
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data.get('phone', ''),
                    reason=form.cleaned_data['reason'],
                    source=form.cleaned_data.get('source', ''),
                    message=form.cleaned_data['message'],
                    ip_address=client_ip,
                    user_agent=user_agent[:500] if user_agent else ''  # Truncate if too long
                )
                
                # Send email notifications
                email_sent = send_contact_emails(form.cleaned_data, contact_submission)
                
                if email_sent:
                    contact_submission.email_sent = True
                    contact_submission.email_sent_at = timezone.now()
                    contact_submission.save()
                
                # Success message based on reason
                success_message = get_success_message(form.cleaned_data['reason'])
                messages.success(request, success_message)
                
                # Log successful submission
                logger.info(f"Contact form submitted successfully by {form.cleaned_data['email']} - Reason: {form.cleaned_data['reason']}")
                
                # Redirect to prevent re-submission
                return HttpResponseRedirect(reverse('contact') + '?success=1')
                
            except Exception as e:
                logger.error(f"Error processing contact form: {str(e)}")
                messages.error(
                    request,
                    'There was an error processing your request. Please try again later or call us directly at +91 987 952 1234.'
                )
        else:
            # Form has validation errors
            messages.error(
                request,
                'Please correct the errors below and try again.'
            )
            logger.warning(f"Contact form validation failed: {form.errors}")
    else:
        form = ContactForm()
        
        # Check if coming from success redirect
        if request.GET.get('success'):
            messages.info(
                request,
                'Thank you! We have received your message and will contact you within 24 hours.'
            )
    
    # Get recent contact statistics for display (optional)
    context = {
        'form': form,
        'page_title': 'Contact Us - Drive RP',
        'contact_info': get_contact_info(),
        'business_hours': get_business_hours(),
    }
    
    return render(request, 'contact.html', context)


def send_contact_emails(form_data, submission_instance):
    """
    Send email notifications for contact form submissions
    Returns True if emails sent successfully, False otherwise
    """
    try:
        # Prepare email context
        email_context = {
            'name': form_data['name'],
            'email': form_data['email'],
            'phone': form_data.get('phone', 'Not provided'),
            'reason': form_data['reason'],
            'reason_display': dict(ContactForm.REASON_CHOICES)[form_data['reason']],
            'source': form_data.get('source', 'Not specified'),
            'source_display': dict(ContactForm.SOURCE_CHOICES).get(form_data.get('source', ''), 'Not specified'),
            'message': form_data['message'],
            'submission_date': submission_instance.created_at,
            'submission_id': str(submission_instance.id),
        }
        
        # Send admin notification email
        admin_subject = f"New {email_context['reason_display']} Inquiry - Drive RP"
        send_admin_notification(admin_subject, email_context)
        
        # Send user confirmation email
        user_subject = get_user_email_subject(form_data['reason'])
        send_user_confirmation(user_subject, email_context)
        
        logger.info(f"Contact form emails sent successfully for submission {submission_instance.id}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending contact emails: {str(e)}")
        return False


def send_admin_notification(subject, context):
    """Send notification email to admin"""
    try:
        # Render email template
        html_message = render_to_string('emails/contact_admin_notification.html', context)
        text_message = render_to_string('emails/contact_admin_notification.txt', context)
        
        admin_email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[getattr(settings, 'CONTACT_EMAIL', 'admin@driverp.in')],
            reply_to=[context['email']]
        )
        admin_email.content_subtype = "html"
        admin_email.send()
        
    except Exception as e:
        logger.error(f"Error sending admin notification: {str(e)}")
        raise


def send_user_confirmation(subject, context):
    """Send confirmation email to user"""
    try:
        # Render email template
        html_message = render_to_string('emails/contact_user_confirmation.html', context)
        text_message = render_to_string('emails/contact_user_confirmation.txt', context)
        
        user_email = EmailMessage(
            subject=subject,
            body=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[context['email']]
        )
        user_email.content_subtype = "html"
        user_email.send()
        
    except Exception as e:
        logger.error(f"Error sending user confirmation: {str(e)}")
        raise


def get_success_message(reason):
    """Get customized success message based on inquiry reason"""
    success_messages = {
        'general_enquiry': 'Thank you for your inquiry! Our team will get back to you within 24 hours.',
        'buy_bike': 'Thank you for your interest in buying a bike! Our sales team will contact you soon with available options.',
        'sell_bike': 'Thank you for choosing Drive RP to sell your bike! Our evaluation team will contact you to schedule an assessment.',
        'exchange_bike': 'Thank you for your bike exchange inquiry! Our team will contact you to discuss exchange options and valuations.',
        'rto_service': 'Thank you for your RTO service inquiry! Our documentation team will contact you with the required process and documents.',
        'others': 'Thank you for contacting Drive RP! We will get back to you shortly.',
    }
    return success_messages.get(reason, 'Thank you for contacting us! We will get back to you soon.')


def get_user_email_subject(reason):
    """Get customized email subject for user confirmation"""
    subjects = {
        'general_enquiry': 'Thank you for contacting Drive RP',
        'buy_bike': 'Thank you for your interest in buying a bike - Drive RP',
        'sell_bike': 'Thank you for choosing Drive RP to sell your bike',
        'exchange_bike': 'Thank you for your bike exchange inquiry - Drive RP',
        'rto_service': 'Thank you for your RTO service inquiry - Drive RP',
        'others': 'Thank you for contacting Drive RP',
    }
    return subjects.get(reason, 'Thank you for contacting Drive RP')


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def get_contact_info():
    """Get contact information for template"""
    return {
        'address': '51, Rajaji Street, GST Road, Chengalpattu-603104, Tamil Nadu, India',
        'phone': '+91 987 952 1234',
        'email': 'info@driverp.in',
        'website': 'www.DriveRp.in'
    }


def get_business_hours():
    """Get business hours for template"""
    return {
        'monday_friday': '9:00 AM - 7:00 PM',
        'saturday': '9:00 AM - 5:00 PM',
        'sunday': '10:00 AM - 4:00 PM'
    }


# AJAX endpoint for real-time form validation
@csrf_protect
@require_http_methods(["POST"])
def validate_contact_field(request):
    """AJAX endpoint for real-time field validation"""
    try:
        field_name = request.POST.get('field_name')
        field_value = request.POST.get('field_value')
        
        if not field_name or field_value is None:
            return JsonResponse({'valid': False, 'error': 'Missing field data'})
        
        # Create a form with just this field to validate
        form_data = {field_name: field_value}
        form = ContactForm(form_data)
        
        # Validate just this field
        if field_name in form.fields:
            try:
                form.full_clean()
                field_errors = form.errors.get(field_name, [])
                
                if field_errors:
                    return JsonResponse({
                        'valid': False,
                        'error': field_errors[0]
                    })
                else:
                    return JsonResponse({'valid': True})
                    
            except Exception:
                return JsonResponse({
                    'valid': False,
                    'error': 'Validation error'
                })
        
        return JsonResponse({'valid': False, 'error': 'Invalid field'})
        
    except Exception as e:
        logger.error(f"AJAX validation error: {str(e)}")
        return JsonResponse({'valid': False, 'error': 'Server error'})


# API endpoint for contact submissions (optional)
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View

@method_decorator(csrf_exempt, name='dispatch')
class ContactAPIView(View):
    """API endpoint for contact form submissions"""
    
    def post(self, request):
        try:
            # Parse JSON data
            if request.content_type == 'application/json':
                data = json.loads(request.body.decode('utf-8'))
            else:
                data = request.POST.dict()
            
            form = ContactForm(data)
            
            if form.is_valid():
                # Save submission
                contact_submission = ContactSubmission.objects.create(
                    name=form.cleaned_data['name'],
                    email=form.cleaned_data['email'],
                    phone=form.cleaned_data.get('phone', ''),
                    reason=form.cleaned_data['reason'],
                    source=form.cleaned_data.get('source', ''),
                    message=form.cleaned_data['message'],
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
                )
                
                # Send emails
                email_sent = send_contact_emails(form.cleaned_data, contact_submission)
                
                if email_sent:
                    contact_submission.email_sent = True
                    contact_submission.email_sent_at = timezone.now()
                    contact_submission.save()
                
                return JsonResponse({
                    'success': True,
                    'message': get_success_message(form.cleaned_data['reason']),
                    'submission_id': str(contact_submission.id)
                })
            else:
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                }, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            logger.error(f"Contact API error: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': 'An error occurred. Please try again.'
            }, status=500)
    
    def get(self, request):
        """API info endpoint"""
        return JsonResponse({
            'name': 'Drive RP Contact API',
            'version': '1.0',
            'endpoints': {
                'POST /contact/api/': 'Submit contact form',
                'POST /contact/validate/': 'Validate individual fields'
            }
        })


# Admin dashboard view for contact submissions
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, Q
from django.utils.dateparse import parse_date

@staff_member_required
def contact_dashboard(request):
    """Dashboard for contact form submissions (admin only)"""
    try:
        # Get date range from request
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        # Base queryset
        submissions = ContactSubmission.objects.all()
        
        # Apply date filters
        if start_date:
            start_date = parse_date(start_date)
            if start_date:
                submissions = submissions.filter(created_at__date__gte=start_date)
        
        if end_date:
            end_date = parse_date(end_date)
            if end_date:
                submissions = submissions.filter(created_at__date__lte=end_date)
        
        # Get statistics
        stats = {
            'total_submissions': submissions.count(),
            'pending_submissions': submissions.filter(status='new').count(),
            'resolved_submissions': submissions.filter(status='resolved').count(),
            'by_reason': submissions.values('reason').annotate(count=Count('reason')),
            'by_source': submissions.values('source').annotate(count=Count('source')),
            'recent_submissions': submissions.order_by('-created_at')[:10]
        }
        
        return render(request, 'admin/contact_dashboard.html', {
            'stats': stats,
            'submissions': submissions.order_by('-created_at'),
        })
        
    except Exception as e:
        logger.error(f"Dashboard error: {str(e)}")
        messages.error(request, 'Error loading dashboard data.')
        return redirect('admin:index')


# Bulk actions for admin
@staff_member_required
@require_http_methods(["POST"])
def bulk_update_submissions(request):
    """Bulk update contact submissions status"""
    try:
        submission_ids = request.POST.getlist('submission_ids')
        action = request.POST.get('action')
        
        if not submission_ids or not action:
            messages.error(request, 'Missing required data.')
            return redirect('contact_dashboard')
        
        submissions = ContactSubmission.objects.filter(id__in=submission_ids)
        
        if action == 'mark_resolved':
            submissions.update(status='resolved', assigned_to=request.user)
            messages.success(request, f'Marked {submissions.count()} submissions as resolved.')
        elif action == 'mark_in_progress':
            submissions.update(status='in_progress', assigned_to=request.user)
            messages.success(request, f'Marked {submissions.count()} submissions as in progress.')
        elif action == 'delete':
            count = submissions.count()
            submissions.delete()
            messages.success(request, f'Deleted {count} submissions.')
        
        return redirect('contact_dashboard')
        
    except Exception as e:
        logger.error(f"Bulk update error: {str(e)}")
        messages.error(request, 'Error updating submissions.')
        return redirect('contact_dashboard')




def auth_view(request):
    # Get latest images for login and register forms
    login_image = AuthImage.objects.filter(is_for_login=True).order_by("-uploaded_at").first()
    register_image = AuthImage.objects.filter(is_for_register=True).order_by("-uploaded_at").first()

    context = {
        "login_image": login_image,
        "register_image": register_image,
    }
    return render(request, "auth.html", context)


from django.http import JsonResponse
from .models import Motorcycle

# Form submission page
def sell_motorcycle(request):
    if request.method == 'POST':
        brand = request.POST.get('brandName')
        model_name = request.POST.get('model')
        variant = request.POST.get('variant')
        year = int(request.POST.get('year'))
        kms_driven = int(request.POST.get('kmsDriven'))
        owner = request.POST.get('owner')

        # Simple price calculation
        base_prices = {
            'Honda': 80000, 'Yamaha': 85000, 'Kawasaki': 120000, 'Suzuki': 75000,
            'KTM': 100000, 'Bajaj': 70000, 'TVS': 65000, 'Royal Enfield': 110000,
            'Hero': 55000, 'Ducati': 800000, 'BMW': 300000, 'Harley Davidson': 600000
        }
        base_price = base_prices.get(brand, 75000)
        current_year = 2025  # can use datetime.now().year
        age = current_year - year
        base_price = base_price * (0.9 ** age)
        base_price = base_price * (1 - (kms_driven / 1000) * 0.005)

        owner_factors = {
            '1st Owner': 1.0,
            '2nd Owner': 0.85,
            '3rd Owner': 0.7,
            '4th Owner': 0.6,
            '5+ Owner': 0.5
        }
        base_price = base_price * owner_factors.get(owner, 0.8)
        estimated_price = round(base_price)

        motorcycle = Motorcycle.objects.create(
            brand=brand,
            model=model_name,
            variant=variant,
            year=year,
            kms_driven=kms_driven,
            owner=owner,
            estimated_price=estimated_price
        )

        return JsonResponse({'estimated_price': estimated_price, 'message': 'Motorcycle saved successfully'})

    return render(request, 'sell_motorcycle.html')
