from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.template import loader
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Count
from django.conf import settings
import os

# Import Models
from django.contrib.auth import get_user_model
from families.models import Family
from expenses.models import Expense
from notes.models import Note
from udhar.models import Udhar

User = get_user_model()

def is_superuser(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_superuser, login_url='/login/')

@user_passes_test(is_superuser, login_url='/login/')
def admin_dashboard_view(request):
    """
    Superadmin Dashboard View.
    Only accessible by superusers.
    """
    # 1. User Stats
    total_users = User.objects.count()
    active_users_24h = User.objects.filter(is_active=True).count() # Simplified, usually check last_login

    # 2. App Data Stats
    total_families = Family.objects.count()
    total_expenses = Expense.objects.count()
    total_notes = Note.objects.count()
    total_udhar = Udhar.objects.count()

    # 3. Storage Stats (Approximate DB size)
    db_path = settings.DATABASES['default']['NAME']
    db_size = 0
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path)
    
    # Format DB Size
    def format_size(size):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.2f} {unit}"
            size /= 1024
        return f"{size:.2f} TB"

    db_size_formatted = format_size(db_size)

    # 4. Recent Users
    recent_users = User.objects.order_by('-date_joined')[:5]

    context = {
        'total_users': total_users,
        'active_users': active_users_24h,
        'total_families': total_families,
        'total_expenses': total_expenses,
        'total_notes': total_notes,
        'total_udhar': total_udhar,
        'db_size': db_size_formatted,
        'recent_users': recent_users
    }

    return render(request, 'dashboard.html', context)

def admin_login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        # We use 'email' as username in some places, but authenticate expects username usually 
        # unless overridden. Let's try both or rely on how your auth is set up.
        # Assuming username=email or passed directly.
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            if user.is_superuser:
                login(request, user)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('admin_dashboard')
            else:
                messages.error(request, "Access Denied. Superadmin only.")
        else:
            messages.error(request, "Invalid credentials.")
            
    return render(request, 'admin_login.html')

def admin_logout_view(request):
    logout(request)
    return redirect('admin_login')

def custom_page_not_found_view(request, exception=None):
    """
    Custom 404 handler. 
    Returns JSON if the request path starts with /api/, otherwise HTML.
    """
    if request.path.startswith('/api/'):
        return JsonResponse({'error': 'Not Found', 'message': 'The requested resource was not found.'}, status=404)
    return render(request, "404.html", status=404)

def custom_error_view(request):
    """
    Custom 500 handler.
    Returns JSON if the request path starts with /api/, otherwise HTML.
    """
    if request.path.startswith('/api/'):
        return JsonResponse({'error': 'Server Error', 'message': 'An internal server error occurred.'}, status=500)
    return render(request, "500.html", status=500)

def custom_permission_denied_view(request, exception=None):
    """
    Custom 403 handler.
    Returns JSON if the request path starts with /api/, otherwise HTML.
    """
    if request.path.startswith('/api/'):
        return JsonResponse({'error': 'Forbidden', 'message': 'You do not have permission to perform this action.'}, status=403)
    return render(request, "403.html", status=403)

def custom_bad_request_view(request, exception=None):
    """
    Custom 400 handler.
    """
    if request.path.startswith('/api/'):
        return JsonResponse({'error': 'Bad Request', 'message': 'The request could not be understood.'}, status=400)
    return render(request, "404.html", status=400) # Reusing 404 template or could create 400.html, usually 404 is fine or generic error

@user_passes_test(is_superuser, login_url='/login/')
def communications_view(request):
    """
    Renders the Communications Center for sending Emails and Notifications.
    """
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    
    # Estimate devices
    from users.models import Profile
    total_devices = Profile.objects.exclude(fcm_token__isnull=True).exclude(fcm_token__exact='').count()
    
    context = {
        'total_users': total_users,
        'active_users': active_users,
        'total_devices': total_devices
    }
    return render(request, 'admin/communications.html', context)

@user_passes_test(is_superuser, login_url='/login/')
def send_bulk_email(request):
    if request.method != 'POST':
        return redirect('communications')
        
    recipient_type = request.POST.get('recipient_type')
    subject = request.POST.get('subject')
    body = request.POST.get('body')
    
    users = User.objects.none()
    if recipient_type == 'all':
        users = User.objects.all()
    elif recipient_type == 'active':
        users = User.objects.filter(is_active=True)
    elif recipient_type == 'staff':
        users = User.objects.filter(is_staff=True)
        
    success_count = 0
    fail_count = 0
    failed_emails = []
    
    from django.core.mail import send_mail
    from django.conf import settings
    
    # In a real-world scenario, use a background task (Celery)
    for user in users:
        if user.email:
            try:
                send_mail(
                    subject=subject,
                    message="", # Plain text fallback
                    html_message=body,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False
                )
                success_count += 1
            except Exception as e:
                fail_count += 1
                failed_emails.append(f"{user.email}: {str(e)}")
    
    # Store results in session to show on redirect
    # But for a simple admin dashboard, let's just render the page again with context
    # Usually better to redirect to avoid form resubmission, but here we want to show logs immediately.
    
    # Re-fetch stats
    from users.models import Profile
    total_devices = Profile.objects.exclude(fcm_token__isnull=True).exclude(fcm_token__exact='').count()
    
    context = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_devices': total_devices,
        'email_results': {
            'success_count': success_count,
            'fail_count': fail_count,
            'failed_emails': failed_emails
        }
    }
    return render(request, 'admin/communications.html', context)

@user_passes_test(is_superuser, login_url='/login/')
def send_bulk_notification(request):
    if request.method != 'POST':
        return redirect('communications')
        
    title = request.POST.get('title')
    message = request.POST.get('message')
    data_json = request.POST.get('data_json')
    
    data = None
    if data_json:
        import json
        try:
            data = json.loads(data_json)
        except:
             # If invalid JSON, just ignore or send empty
             pass
             
    from users.models import Profile
    from users.notification_manager import NotificationManager
    
    # Get all valid tokens
    profiles = Profile.objects.exclude(fcm_token__isnull=True).exclude(fcm_token__exact='')
    tokens = [p.fcm_token for p in profiles]
    
    success = 0
    failure = 0
    
    if tokens:
        try:
            # Note: send_multicast returns a batch response object
            # We need to construct a robust way to capture results if we want detailed logs from FCM
            # Our NotificationManager logs to console, but let's try to capture basic success/fail here
            # Ideally NotificationManager should return stats.
            
            # Let's assume NotificationManager handles it safely. Use a custom call here for better control/stats if needed
            # Or modify NotificationManager later to return stats.
            # For now, we will trust the FireBase SDK response if we access it directly, 
            # OR just wrap the manager call.
            
            result = NotificationManager.send_multicast_notification(tokens, title, message, data)
            
            if result:
                success = result.get('success_count', 0)
                failure = result.get('failure_count', 0)
                
                # Update UI message
                context_msg = f"Sent: {success}, Failed: {failure}"
                if result.get('error'):
                    context_msg += f" (Error: {result.get('error')})"
            else:
                 # Should not happen with new manager logic
                 failure = len(tokens)
                 context_msg = "Failed to initiate sending"

        except Exception as e:
            failure = len(tokens)
            context_msg = f"Error: {str(e)}"
    else:
        context_msg = "No devices found with tokens."
    
    # Re-fetch stats
    total_devices = profiles.count()
    
    context = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_devices': total_devices,
        'notif_results': {
            'success': context_msg,
            'failure': failure
        }
    }
    return render(request, 'admin/communications.html', context)
