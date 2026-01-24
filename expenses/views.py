from rest_framework import viewsets, permissions
from .models import Expense
from .serializers import ExpenseSerializer

class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Expense.objects.filter(family__members=self.request.user).distinct()

    def perform_create(self, serializer):
        user = self.request.user
        family = user.families.first()
        
        # If no family, just save (or handle error, but keeping existing behavior)
        instance = serializer.save(user=user, family=family)

        if family:
            try:
                # Get all members of the family except the creator
                members = family.members.exclude(id=user.id)
                
                tokens = []
                for member in members:
                    if hasattr(member, 'profile') and member.profile.fcm_token:
                        tokens.append(member.profile.fcm_token)
                
                if tokens:
                    from users.notification_manager import NotificationManager
                    title = "New Expense Added"
                    name_display = user.first_name if user.first_name else user.username
                    body = f"{name_display} added an expense of ₹{instance.amount}"
                    if instance.items:
                        body += f" for {instance.items}"
                    
                    NotificationManager.send_multicast_notification(
                        tokens=tokens,
                        title=title,
                        body=body,
                        data={
                            "type": "new_expense",
                            "expense_id": str(instance.id),
                            "family_id": str(family.id)
                        }
                    )
            except Exception as e:
                print(f"Error sending notification: {e}")

