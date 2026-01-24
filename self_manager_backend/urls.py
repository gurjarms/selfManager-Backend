from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Import viewsets
from attendance.views import AttendanceViewSet
from notes.views import NoteViewSet
from families.views import FamilyViewSet, FamilyMemberViewSet, invite_bridge
from expenses.views import ExpenseViewSet
from udhar.views import UdharViewSet
from users.views import RegisterView, MeView, SendOTPView, VerifyOTPView, ResetPasswordView, GoogleLoginView, UpdateFCMTokenView, DeleteAccountView, CustomTokenObtainPairView

router = routers.DefaultRouter()
router.register(r'attendance', AttendanceViewSet, basename='attendance')
router.register(r'notes', NoteViewSet, basename='notes')
router.register(r'families', FamilyViewSet, basename='families')
router.register(r'family-members', FamilyMemberViewSet, basename='family-members')
router.register(r'expenses', ExpenseViewSet, basename='expenses')
router.register(r'udhar', UdharViewSet, basename='udhar')

from django.conf import settings
from django.conf.urls.static import static

from .views import (
    custom_page_not_found_view, 
    custom_error_view, 
    custom_permission_denied_view, 
    custom_bad_request_view,
    admin_dashboard_view,
    admin_login_view,
    admin_logout_view,
    communications_view,
    send_bulk_email,
    send_bulk_notification
)

urlpatterns = [
    path('', admin_dashboard_view, name='admin_dashboard'),
    path('dashboard/', admin_dashboard_view, name='admin_dashboard_alt'),
    path('dashboard/communications/', communications_view, name='communications'),
    path('dashboard/communications/send-email/', send_bulk_email, name='send_bulk_email'),
    path('dashboard/communications/send-notify/', send_bulk_notification, name='send_bulk_notification'),
    path('dashboard/login/', admin_login_view, name='admin_login'),
    path('dashboard/logout/', admin_logout_view, name='admin_logout'),
    path('admin/', admin.site.urls),
    path('api/auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/register/', RegisterView.as_view(), name='auth_register'),
    path('api/auth/google-login/', GoogleLoginView.as_view(), name='auth_google_login'),
    path('api/auth/send-otp/', SendOTPView.as_view(), name='auth_send_otp'),
    path('api/auth/verify-otp/', VerifyOTPView.as_view(), name='auth_verify_otp'),
    path('api/auth/reset-password/', ResetPasswordView.as_view(), name='auth_reset_password'),
    path('api/users/update-fcm-token/', UpdateFCMTokenView.as_view(), name='update_fcm_token'),
    path('api/users/delete-account/', DeleteAccountView.as_view(), name='delete_account'),
    path('api/users/me/', MeView.as_view(), name='user_me'),
    path('api/chat/', include('chat.urls')),
    path('api/', include(router.urls)),
    path('families/invite/<code>/', invite_bridge, name='family_invite'),
    
    # Direct Access for Error Pages
    path('404/', custom_page_not_found_view),
    path('500/', custom_error_view),
    path('403/', custom_permission_denied_view),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'self_manager_backend.views.custom_page_not_found_view'
handler500 = 'self_manager_backend.views.custom_error_view'
handler403 = 'self_manager_backend.views.custom_permission_denied_view'
handler400 = 'self_manager_backend.views.custom_bad_request_view'


