from django.contrib import admin
from .models import Message

class MessageAdmin(admin.ModelAdmin):
    list_display = ('family', 'sender', 'content', 'timestamp')
    search_fields = ('sender__username', 'content')
    list_filter = ('family', 'sender')


admin.site.register(Message, MessageAdmin)
    