from django import template
from django.contrib.auth import get_user_model
from families.models import Family
from expenses.models import Expense
from notes.models import Note
from udhar.models import Udhar
from django.conf import settings
import os

register = template.Library()

@register.simple_tag
def get_dashboard_stats():
    User = get_user_model()
    
    # DB Size
    db_path = settings.DATABASES['default']['NAME']
    db_size_formatted = "Unknown"
    if os.path.exists(db_path):
        size = os.path.getsize(db_path)
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                db_size_formatted = f"{size:.2f} {unit}"
                break
            size /= 1024
    
    return {
        'total_users': User.objects.count(),
        'total_families': Family.objects.count(),
        'total_expenses': Expense.objects.count(),
        'total_notes': Note.objects.count(),
        'total_udhar': Udhar.objects.count(),
        'db_size': db_size_formatted
    }
