from django.db import models
from django.conf import settings
from families.models import Family

class Message(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='chat_images/', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Simple message type distinction (text vs image vs system)
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('system', 'System'),
    )
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPES, default='text')
    is_deleted = models.BooleanField(default=False)
    is_edited = models.BooleanField(default=False)
    reply_to = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"

class MessageReadStatus(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='read_messages')
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')

    def __str__(self):
        return f"Read by {self.user.username} at {self.read_at}"
