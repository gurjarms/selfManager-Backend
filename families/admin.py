from django.contrib import admin
from .models import Family, FamilyMember

@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner')
    search_fields = ('name', 'owner__username')


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    list_display = ('family', 'user', 'joined_at')
    list_filter = ('joined_at',)
    search_fields = ('family__name', 'user__username')
