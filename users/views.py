from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from .serializers import UserSerializer, RegisterSerializer, SendOTPSerializer, VerifyOTPSerializer, ForgotPasswordSerializer, GoogleLoginSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import OTPRequest
from django.core.mail import send_mail
from django.conf import settings
import random
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class SendOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            is_forgot = request.data.get('is_forgot', False)
            
            user_exists = User.objects.filter(email=email).exists()
            
            if is_forgot:
                 if not user_exists:
                     return Response({"email": ["User not found."]}, status=status.HTTP_404_NOT_FOUND)
                 title = "Reset Your Password"
                 message_top = "We received a request to reset your password for your Self Manager account."
                 message_bottom = "If you didn't request this, you can safely ignore this email."
            else:
                # Registration check
                if user_exists:
                     return Response({"email": ["Email already registered."]}, status=status.HTTP_400_BAD_REQUEST)
                title = "Welcome to Self Manager!"
                message_top = "Thank you for joining us! Please use the following code to verify your email address and complete your registration."
                message_bottom = "This code will expire shortly. Please do not share it with anyone."

            # Generate OTP
            otp = str(random.randint(1000000, 9999999))
            
            # Save
            OTPRequest.objects.create(email=email, otp=otp)
            
            # HTML Email Template
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background-color: #0f172a; color: #f8fafc; }}
                    .container {{ max-width: 600px; margin: 40px auto; background-color: #1e293b; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.5); border: 1px solid #334155; }}
                    .header {{ background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); padding: 40px 20px; text-align: center; }}
                    .header h1 {{ margin: 0; font-size: 28px; font-weight: 800; letter-spacing: -0.5px; color: white; text-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
                    .content {{ padding: 40px; text-align: center; line-height: 1.6; }}
                    .title {{ font-size: 22px; font-weight: 700; color: #f8fafc; margin-bottom: 20px; }}
                    .message {{ color: #94a3b8; font-size: 16px; margin-bottom: 30px; }}
                    .otp-box {{ background-color: #020617; padding: 5px; border-radius: 12px; display: inline-block; margin: 10px 0; border: 1px dashed #3b82f6; }}
                    .otp-code {{ font-size: 32px; font-weight: 800; color: #3b82f6; letter-spacing: 12px; margin-left: 12px; }}
                    .footer {{ background-color: #1e293b; padding: 20px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #334155; }}
                    .brand-name {{ color: #3b82f6; font-weight: 600; text-decoration: none; }}
                </style> 
            </head> 
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Self Manager</h1>
                    </div>
                    <div class="content">
                        <div class="title">{title}</div>
                        <div class="message">{message_top}</div>
                        <div class="otp-box">
                            <div class="otp-code">{otp}</div>
                        </div>
                        <div class="message" style="margin-top: 30px;">{message_bottom}</div>
                    </div>
                    <div class="footer">
                        &copy; 2026 <a href="#" class="brand-name">Self Manager</a>. Secure OTP Verification System.
                    </div>
                </div>
            </body>
            </html>
            """

            # Send Email
            print(f"------------\nOTP for {email}: {otp}\n------------") 
            try:
                send_mail(
                    subject=f"Self Manager - {title}",
                    message=f"Your OTP is {otp}", # Fallback
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    html_message=html_content,
                    fail_silently=False,
                )
            except Exception as e:
                print(f"Email send failed: {e}")
                
            return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyOTPView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            otp = serializer.validated_data['otp']
            
            otp_req = OTPRequest.objects.filter(email=email, otp=otp).last()
            if otp_req and otp_req.is_valid():
                otp_req.is_verified = True
                otp_req.save()
                return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)
            
            return Response({"otp": ["Invalid or expired OTP."]}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class MeView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Check if soft deleted
            # Check if soft deleted -> REACTIVATE
            recovered = False
            if hasattr(user, 'profile') and user.profile.is_deleted:
                user.profile.is_deleted = False
                user.profile.deleted_at = None
                user.profile.save()
                recovered = True

            # Login successful, generate tokens
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'recovered': recovered
            }, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateFCMTokenView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token = request.data.get('fcm_token')
        if not token:
            return Response({"error": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        # Ensure profile exists (it should via signal, but safety check)
        if hasattr(user, 'profile'):
            user.profile.fcm_token = token
            user.profile.save()
            return Response({"message": "Device token updated successfully"}, status=status.HTTP_200_OK)
        else:
             # Create logic or error? Signals handle it mostly.
              Profile.objects.create(user=user, fcm_token=token)
              return Response({"message": "Device token saved (new profile)"}, status=status.HTTP_200_OK)

class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request):
        user = request.user
        
        # 1. Check Family Ownership
        # Using the related_name 'owned_families' from Family model
        if hasattr(user, 'owned_families') and user.owned_families.exists():
             return Response(
                 {"error": "You are the owner of one or more families. Please transfer ownership or delete the family before deleting your account."},
                 status=status.HTTP_400_BAD_REQUEST
             )

        if hasattr(user, 'profile'):
            user.profile.is_deleted = True
            from django.utils import timezone
            user.profile.deleted_at = timezone.now()
            user.profile.save()
            return Response({"message": "Account marked for deletion. It will be permanently removed in 30 days."}, status=status.HTTP_200_OK)
        return Response({"error": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
