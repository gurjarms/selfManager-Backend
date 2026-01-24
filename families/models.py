from django.db import models
from django.conf import settings

class Family(models.Model):
    name = models.CharField(max_length=255)
    family_code = models.CharField(max_length=12, unique=True, null=True, blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='owned_families')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, through='FamilyMember', related_name='families')
    allow_join_via_link = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class FamilyMember(models.Model):
    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('family', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.family.name}"

class JoinRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    family = models.ForeignKey(Family, on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='family_join_requests')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('family', 'user')

    def __str__(self):
        return f"{self.user.username} requests to join {self.family.name}"
