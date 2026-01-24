from django.db import models
from django.conf import settings

class Attendance(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=20)  # e.g., 'FULL-DAY', 'HALF-DAY'
    remark = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"{self.user.username} - {self.date} ({self.status})"
