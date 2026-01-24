from rest_framework import serializers
from .models import Family, FamilyMember, JoinRequest

class FamilySerializer(serializers.ModelSerializer):
    owner_username = serializers.ReadOnlyField(source='owner.username')
    
    class Meta:
        model = Family
        fields = ['id', 'name', 'family_code', 'owner', 'owner_username', 'members', 'allow_join_via_link']
        read_only_fields = ['id', 'owner', 'family_code', 'owner_username']

class FamilyMemberSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    first_name = serializers.ReadOnlyField(source='user.first_name')
    
    class Meta:
        model = FamilyMember
        fields = ['id', 'family', 'user', 'username', 'first_name', 'joined_at']
        read_only_fields = ['id', 'joined_at', 'username', 'first_name']

class JoinRequestSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source='user.username')
    first_name = serializers.ReadOnlyField(source='user.first_name')
    last_name = serializers.ReadOnlyField(source='user.last_name')
    family_name = serializers.ReadOnlyField(source='family.name')

    class Meta:
        model = JoinRequest
        fields = ['id', 'family', 'family_name', 'user', 'username', 'first_name', 'last_name', 'status', 'created_at']
        read_only_fields = ['id', 'status', 'created_at']
