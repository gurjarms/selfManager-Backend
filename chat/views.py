from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Message, MessageReadStatus
from .serializers import MessageSerializer
from families.models import Family
from users.notification_manager import NotificationManager
from django.db.models import Q
from users.models import Profile

from rest_framework.pagination import PageNumberPagination

class ChatPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class MessageListCreateView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = ChatPagination

    def get_queryset(self):
        family_id = self.kwargs.get('family_id')
        user = self.request.user
        # Ensure user is member of family
        family = get_object_or_404(Family, id=family_id)
        if user not in family.members.all():
            return Message.objects.none()
        
        # Order by timestamp descending (newest first) for efficient pagination
        return Message.objects.filter(family=family).order_by('-timestamp')

    def perform_create(self, serializer):
        family_id = self.kwargs.get('family_id')
        family = get_object_or_404(Family, id=family_id)
        user = self.request.user

        if user not in family.members.all():
            raise permissions.PermissionDenied("You are not a member of this family.")

        message = serializer.save(sender=user, family=family)

        # --- Send Notifications ---
        # Get all other members
        other_members = family.members.exclude(id=user.id)
        
        # Collect tokens
        tokens = []
        for member in other_members:
            try:
                if hasattr(member, 'profile') and member.profile.fcm_token:
                    tokens.append(member.profile.fcm_token)
            except Exception:
                pass

        if tokens:
            sender_name = user.first_name if user.first_name else user.username
            body = message.content if message.content else "Sent an image"
            
            NotificationManager.send_multicast_notification(
                tokens=tokens,
                title=f"{sender_name} in {family.name}",
                body=body,
                data={
                    "type": "chat_message",
                    "family_id": str(family.id),
                    "message_id": str(message.id),
                    "sender_id": str(user.id)
                }
            )

class MarkReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, family_id):
        # Mark all unread messages in this family as read for current user
        # or specific messages if passed
        user = request.user
        
        # We generally mark ALL messages in family <= last_seen_id as read?
        # Or simplistic: Get all messages in family where I don't have a ReadStatus
        
        family = get_object_or_404(Family, id=family_id)
        if user not in family.members.all():
            return Response({"error": "Not a member"}, status=status.HTTP_403_FORBIDDEN)

        # Find messages not read by me
        unread_messages = Message.objects.filter(family=family).exclude(
            read_statuses__user=user
        )

        created_count = 0
        for msg in unread_messages:
            _, created = MessageReadStatus.objects.get_or_create(message=msg, user=user)
            if created:
                created_count += 1
        
        return Response({"status": "success", "marked_read": created_count})

from django.utils import timezone
from datetime import timedelta

class MessageDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Message.objects.all()
    lookup_field = 'id'

    def perform_update(self, serializer):
        message = self.get_object()
        if message.sender != self.request.user:
            raise permissions.PermissionDenied("You can only edit your own messages.")
        
        if message.is_deleted:
             raise permissions.PermissionDenied("Cannot edit a deleted message.")
        
        # Check editing window (15 minutes)
        if timezone.now() - message.timestamp > timedelta(minutes=15):
             raise permissions.PermissionDenied("You can only edit messages within 15 minutes of sending.")
             
        serializer.save(is_edited=True)

    def perform_destroy(self, instance):
        if instance.sender != self.request.user:
             raise permissions.PermissionDenied("You can only delete your own messages.")
        
        # Hard delete
        instance.delete()
