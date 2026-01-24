from django.contrib import admin
from .models import Expense

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('family', 'user', 'amount', 'category', 'date')
    list_filter = ('date', 'category')
    search_fields = ('family__name', 'user__username', 'description')
