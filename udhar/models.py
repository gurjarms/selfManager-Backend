from django.db import models
from django.conf import settings

class Udhar(models.Model):
    TYPE_CHOICES = [
        ('GIVE', 'GAVE MONEY'),
        ('TAKE', 'TOOK MONEY'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='udhars')
    person_name = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True) # Percentage per month
    date = models.DateField() # When the transaction happened
    due_date = models.DateField(null=True, blank=True)
    reason = models.TextField(blank=True)
    type = models.CharField(max_length=4, choices=TYPE_CHOICES)
    is_closed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.type} - {self.person_name} - {self.amount}"

class Repayment(models.Model):
    udhar = models.ForeignKey(Udhar, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateTimeField()
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Repayment {self.amount} for {self.udhar.person_name}"
