from rest_framework import serializers
from .models import Expense

class ExpenseSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Expense
        fields = ['id', 'family', 'user', 'username', 'amount', 'category', 'date', 'description', 'items', 'image', 'uuid']
        read_only_fields = ['id', 'user']

