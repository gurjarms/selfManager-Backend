from rest_framework import serializers
from django.contrib.auth.models import User
from .models import OTPRequest
import re
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Check for soft delete and REACTIVATE
        recovered = False
        if hasattr(self.user, 'profile') and self.user.profile.is_deleted:
            self.user.profile.is_deleted = False
            self.user.profile.deleted_at = None
            self.user.profile.save()
            recovered = True
            
        data['recovered'] = recovered
        return data

def validate_password_strength(value):
    if len(value) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")
    if not re.search(r'[A-Z]', value):
        raise serializers.ValidationError("Password must contain at least one uppercase letter.")
    if not re.search(r'\d', value):
        raise serializers.ValidationError("Password must contain at least one digit.")
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise serializers.ValidationError("Password must contain at least one special character.")
    return value

def validate_phone_format(value):
    if value and not re.match(r'^[6-9]\d{9}$', value):
         raise serializers.ValidationError("Phone number must be 10 digits and start with 6, 7, 8, or 9.")
    return value

class UserSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(source='profile.phone_number', required=False, allow_blank=True)

    def validate_phone_number(self, value):
        return validate_phone_format(value)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone_number']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        phone_number = profile_data.get('phone_number')
        
        # Update User fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update Profile fields
        if phone_number is not None:
            # Ensure profile exists
            if not hasattr(instance, 'profile'):
                 from .models import Profile
                 Profile.objects.create(user=instance)
            
            instance.profile.phone_number = phone_number
            instance.profile.save()
            
        return instance

class SendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=7)

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    otp = serializers.CharField(write_only=True)
    # email is required
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name', 'last_name', 'otp']

    def validate_first_name(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Name must be at least 3 characters long.")
        return value

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate(self, attrs):
        email = attrs.get('email')  
        otp = attrs.get('otp')
        
        if otp == "google":
             # "google" = Registering new user with Google (Set Password flow)
             # User must NOT exist (or we raise 'Email already registered' below)
             # OTP check bypassed.
             pass
        else:        
            # Standard OTP Flow
            valid_otp = OTPRequest.objects.filter(email=email, otp=otp, is_verified=True).last()
            if not valid_otp or not valid_otp.is_valid():
                 raise serializers.ValidationError({"otp": "Invalid or expired verified OTP. Please verify OTP first."})

        # Check for duplicate email
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "Email already registered."})

        return attrs

    def create(self, validated_data):
        validated_data.pop('otp', None)
        user = User.objects.create_user(**validated_data)
        return user

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=7)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        return validate_password_strength(value)

    def validate(self, attrs):
        email = attrs.get('email')
        otp = attrs.get('otp')
        
        # 1. Check User
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError({"email": "User with this email does not exist."})

        # 2. Check Verification
        valid_otp = OTPRequest.objects.filter(email=email, otp=otp, is_verified=True).last()
        if not valid_otp or not valid_otp.is_valid():
             raise serializers.ValidationError({"otp": "Invalid or expired verified OTP. Please verify OTP first."})
             
        return attrs

    def save(self):
        email = self.validated_data['email']
        new_password = self.validated_data['new_password']
        
        user = User.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        
        # Invalidate OTP to prevent reuse
        OTPRequest.objects.filter(email=email, is_verified=True).delete()
        return user

class GoogleLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, attrs):
        email = attrs.get('email')
        
        # Check if user exists (Case Insensitive)
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise serializers.ValidationError({"detail": "User not found."})
            
        # Check if password is set
        if not user.has_usable_password():
             raise serializers.ValidationError({"detail": "Password not set.", "code": "password_not_set"})
             
        # Return the user object to the View
        attrs['user'] = user
        return attrs
