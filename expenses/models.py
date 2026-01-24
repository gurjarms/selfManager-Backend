from django.db import models
from django.conf import settings

class Expense(models.Model):
    family = models.ForeignKey('families.Family', on_delete=models.CASCADE, related_name='expenses', null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, blank=True)
    date = models.DateField()
    description = models.TextField(blank=True)
    uuid = models.CharField(max_length=100, unique=True, null=True, blank=True)
    items = models.JSONField(default=list, blank=True)
    image = models.ImageField(upload_to='expenses/', null=True, blank=True)

    class Meta:
        ordering = ['-date']


    def __str__(self):
        return f"{self.user.username} - {self.amount} on {self.date}"
