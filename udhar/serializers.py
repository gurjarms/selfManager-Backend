from rest_framework import serializers
from .models import Udhar, Repayment

class RepaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Repayment
        fields = '__all__'
        read_only_fields = ['udhar']

class UdharSerializer(serializers.ModelSerializer):
    repayments = RepaymentSerializer(many=True, read_only=True)
    total_paid = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()

    class Meta:
        model = Udhar
        fields = '__all__'
        read_only_fields = ['user', 'is_closed']

    def get_total_paid(self, obj):
        return sum(r.amount for r in obj.repayments.all())

    def get_balance(self, obj):
        # This is a simple balance. Interest calculation will be handled on frontend or as a computed property
        return obj.amount - self.get_total_paid(obj)
