from django.contrib import admin
from .models import Repayment, Udhar

@admin.register(Udhar)
class UdharAdmin(admin.ModelAdmin):
    list_display = ( "user", "person_name", "amount", "rate", "date", "due_date", "reason", "type", "created_at" )
    list_filter = ['amount']
    search_fields = ['user', 'person_name', 'amount']


@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = ( "udhar", "amount", "date", "note", "created_at" )
    list_filter = ['amount']
