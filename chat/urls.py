from django.urls import path
from .views import MessageListCreateView, MarkReadView, MessageDetailView

urlpatterns = [
    path('families/<int:family_id>/messages/', MessageListCreateView.as_view(), name='message-list-create'),
    path('families/<int:family_id>/read/', MarkReadView.as_view(), name='mark-messages-read'),
    path('messages/<int:id>/', MessageDetailView.as_view(), name='message-detail'),
]
