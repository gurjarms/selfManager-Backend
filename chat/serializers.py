from rest_framework import serializers
from .models import Message, MessageReadStatus
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class MessageReadStatusSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    class Meta:
        model = MessageReadStatus
        fields = ['user', 'read_at']

class RepliedMessageSerializer(serializers.ModelSerializer):
    sender = UserSimpleSerializer(read_only=True)
    class Meta:
        model = Message
        fields = ['id', 'content', 'sender', 'timestamp', 'message_type']

class MessageSerializer(serializers.ModelSerializer):
    sender = UserSimpleSerializer(read_only=True)
    read_statuses = MessageReadStatusSerializer(many=True, read_only=True)
    is_me = serializers.SerializerMethodField()
    
    reply_to_detail = RepliedMessageSerializer(source='reply_to', read_only=True)
    reply_to = serializers.PrimaryKeyRelatedField(queryset=Message.objects.all(), write_only=True, required=False, allow_null=True)

    class Meta:
        model = Message
        fields = ['id', 'family', 'sender', 'content', 'image', 'timestamp', 'message_type', 'read_statuses', 'is_me', 'is_deleted', 'is_edited', 'reply_to', 'reply_to_detail']
        read_only_fields = ['sender', 'timestamp', 'family', 'reply_to_detail']

    def get_is_me(self, obj):
        request = self.context.get('request')
        if request and request.user:
            return obj.sender == request.user
        return False
