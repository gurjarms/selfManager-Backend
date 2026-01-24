from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Udhar, Repayment
from .serializers import UdharSerializer, RepaymentSerializer

class UdharViewSet(viewsets.ModelViewSet):
    serializer_class = UdharSerializer

    def get_queryset(self):
        return Udhar.objects.filter(user=self.request.user).order_by('-date')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['post'])
    def add_repayment(self, request, pk=None):
        udhar = self.get_object()
        serializer = RepaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(udhar=udhar)
            
            # Check if fully paid (ignoring interest for simple closure check)
            total_paid = sum(r.amount for r in udhar.repayments.all())
            if total_paid >= udhar.amount:
                # In a more complex system, we'd check against amount + interest
                pass

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def close_udhar(self, request, pk=None):
        udhar = self.get_object()
        udhar.is_closed = True
        udhar.save()
        return Response({'status': 'Udhar closed'})
