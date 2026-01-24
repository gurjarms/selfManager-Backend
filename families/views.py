from django.db import models
from django.http import HttpResponse
from rest_framework import viewsets, permissions
from .models import Family, FamilyMember, JoinRequest
from .serializers import FamilySerializer, FamilyMemberSerializer, JoinRequestSerializer

import random
import string
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

def generate_family_code():
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Family.objects.filter(family_code=code).exists():
            return code

class FamilyViewSet(viewsets.ModelViewSet):
    serializer_class = FamilySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Family.objects.filter(models.Q(owner=self.request.user) | models.Q(members=self.request.user)).distinct()

    def perform_create(self, serializer):
        family = serializer.save(owner=self.request.user, family_code=generate_family_code())
        # Automatically add owner as a member
        FamilyMember.objects.create(family=family, user=self.request.user)

    def perform_update(self, serializer):
        if serializer.instance.owner != self.request.user:
            return Response({'detail': 'Only the family owner can modify family settings.'}, status=status.HTTP_403_FORBIDDEN)
        serializer.save()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.owner != self.request.user:
            return Response({'detail': 'Only the family owner can delete the family.'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['get'])
    def members(self, request, pk=None):
        family = self.get_object()
        members = FamilyMember.objects.filter(family=family)
        return Response(FamilyMemberSerializer(members, many=True).data)

    @action(detail=False, methods=['post'])
    def join(self, request):
        code = request.data.get('family_code')
        is_link = request.data.get('is_link', False)

        if not code:
            return Response({'detail': 'Family code is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            family = Family.objects.get(family_code=code.upper())
            
            # Check if joining via link is disabled
            if is_link and not family.allow_join_via_link:
                return Response({'detail': 'Joining via link is disabled for this family.'}, status=status.HTTP_403_FORBIDDEN)

            if family.members.filter(id=request.user.id).exists():
                return Response({'detail': 'You are already a member of this family'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check for existing pending request
            existing = JoinRequest.objects.filter(family=family, user=request.user, status='pending').first()
            if existing:
                return Response({'detail': 'You have already sent a request to join this family.'}, status=status.HTTP_400_BAD_REQUEST)

            JoinRequest.objects.create(family=family, user=request.user)
            return Response({'detail': 'Join request sent! Waiting for owner approval.'}, status=status.HTTP_201_CREATED)
        except Family.DoesNotExist:
            return Response({'detail': 'Invalid family code'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def pending_requests(self, request, pk=None):
        family = self.get_object()
        if family.owner != request.user:
            return Response({'detail': 'Only the owner can view pending requests.'}, status=status.HTTP_403_FORBIDDEN)
        
        requests = JoinRequest.objects.filter(family=family, status='pending')
        return Response(JoinRequestSerializer(requests, many=True).data)

    @action(detail=True, methods=['post'])
    def handle_request(self, request, pk=None):
        family = self.get_object()
        if family.owner != request.user:
            return Response({'detail': 'Only the owner can handle requests.'}, status=status.HTTP_403_FORBIDDEN)

        request_id = request.data.get('request_id')
        approve = request.data.get('approve') # Boolean

        if request_id is None or approve is None:
            return Response({'detail': 'request_id and approve are required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            join_req = JoinRequest.objects.get(id=request_id, family=family, status='pending')
            if approve:
                join_req.status = 'accepted'
                FamilyMember.objects.get_or_create(family=family, user=join_req.user)
                join_req.save()
                return Response({'detail': 'Request accepted. Member added to family.'})
            else:
                join_req.status = 'rejected'
                join_req.save()
                return Response({'detail': 'Request rejected.'})
        except JoinRequest.DoesNotExist:
            return Response({'detail': 'Join request not found.'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def by_code(self, request):
        code = request.query_params.get('code')
        if not code:
            return Response({'detail': 'Code is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            family = Family.objects.get(family_code=code.upper())
            return Response(FamilySerializer(family).data)
        except Family.DoesNotExist:
            return Response({'detail': 'Family not found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['post'])
    def transfer_ownership(self, request, pk=None):
        family = self.get_object()
        if family.owner != request.user:
            return Response({'detail': 'Only the owner can transfer ownership.'}, status=status.HTTP_403_FORBIDDEN)
        
        new_owner_id = request.data.get('new_owner_id')
        if not new_owner_id:
            return Response({'detail': 'New owner ID is required'}, status=status.HTTP_400_BAD_REQUEST)
            
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            new_owner = User.objects.get(id=new_owner_id)
            
            # Verify the new owner is already a member
            if not family.members.filter(id=new_owner.id).exists():
                return Response({'detail': 'New owner must be a member of the family.'}, status=status.HTTP_400_BAD_REQUEST)
                
            family.owner = new_owner
            family.save()
            return Response(FamilySerializer(family).data)
        except User.DoesNotExist:
            return Response({'detail': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class FamilyMemberViewSet(viewsets.ModelViewSet):
    serializer_class = FamilyMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return FamilyMember.objects.filter(family__members=self.request.user).distinct()

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Allow if it's the user leaving, or if the user is the owner of the family
        if instance.user == request.user or instance.family.owner == request.user:
            return super().destroy(request, *args, **kwargs)
        return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)


def invite_bridge(request, code):
    # This view will be accessed via a browser from a shared link
    # It renders a simple HTML page that redirects to the app scheme
    app_url = f"selfmanager://join/{code}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Joining Family...</title>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
                display: flex; 
                flex-direction: column; 
                align-items: center; 
                justify-content: center; 
                height: 100vh; 
                margin: 0; 
                background: #f8fafc; 
            }}
            .card {{ 
                background: white; 
                padding: 2.5rem; 
                border-radius: 1.5rem; 
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1); 
                text-align: center; 
                max-width: 400px; 
                width: 90%;
            }}
            h2 {{ color: #1e293b; margin-top: 0; font-size: 1.5rem; }}
            p {{ color: #64748b; line-height: 1.6; margin-bottom: 2rem; }}
            .btn {{ 
                display: inline-block; 
                background: #6366f1; 
                color: white; 
                padding: 0.875rem 1.5rem; 
                border-radius: 0.75rem; 
                text-decoration: none; 
                font-weight: 600;
                transition: background 0.2s;
            }}
            .btn:active {{ background: #4f46e5; }}
            .footer {{ margin-top: 2rem; font-size: 0.875rem; color: #94a3b8; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Self Manager</h2>
            <p>We're opening the app so you can join the family. If nothing happens, tap the button below.</p>
            <a href="{app_url}" class="btn">Open Self Manager</a>
            <div class="footer">Family Code: <strong>{code}</strong></div>
        </div>
        <script>
            // Attempt to open the app automatically
            setTimeout(function() {{
                window.location.href = "{app_url}";
            }}, 500);
        </script>
    </body>
    </html>
    """
    return HttpResponse(html_content)
