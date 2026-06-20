from django.contrib import admin
from .models import CustomUser, Project, Notification, Profile

# Register your models here.
admin.site.register(CustomUser)
admin.site.register(Profile)
admin.site.register(Project)
admin.site.register(Notification)