from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db.models import Sum
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User


# ==========================
# User Management Module
# ==========================
class CustomUser(AbstractUser):
    first_name = None
    last_name = None

    USER_TYPE_CHOICES = (
        ("full_time", "Full-Time"),
        ("freelancer", "Freelancer"),
        ("client", "Client"),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"{self.username} ({self.user_type})"

def save(self, commit=True):
    user = super().save(commit=False)
    user.email = self.cleaned_data["email"]

    role = self.cleaned_data["role"]
    if role == "fulltime":   # safeguard
        role = "full_time"

    user.user_type = role

    if commit:
        user.save()
        if user.user_type in ["freelancer", "full_time"]:
            Profile.objects.get_or_create(user=user)
    return user



# ==========================
# Profile Module (for Freelancer & Full-time)
# ==========================from django.conf import settings
# User Type Choices
USER_TYPE_CHOICES = [
    ("freelancer", "Freelancer"),
    ("full_time", "Full Time"),
]

# Availability Choices
AVAILABILITY_CHOICES = (
    ("Remote", "Remote"),
    ("In-Office", "In-Office"),
    ("Hybrid", "Hybrid"),
)

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    user_name = models.CharField(max_length=255, blank=True, null=True) 
    phone = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    # 🔹 User Type (Freelancer / Full Time)
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default="freelancer")

    # 🔹 Only visible for Freelancers
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # 🔹 Monthly salary for full-time employees (new field)
    monthly_salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # 🔹 Skills & Experience
    skills = models.TextField(blank=True, null=True)
    experience = models.TextField(blank=True, null=True)

    # 🔹 Profile Strength
    profile_strength = models.IntegerField(default=0)

    # 🔹 Availability
    availability = models.CharField(max_length=50, choices=AVAILABILITY_CHOICES, blank=True, null=True)

    def calculate_strength(self):
        strength = 0
        if self.user.username:
            strength += 15
        if self.user.email:
            strength += 15
        if self.phone:
            strength += 10
        if self.location:
            strength += 10
        if self.bio:
            strength += 15
        if self.skills:
            strength += 20
        if self.experience:
            strength += 15
        return min(strength, 100)

    def __str__(self):
        return f"{self.user.username} - {self.user_type}"
    
    @property
    def skills_display(self):
        if self.skills:
            return [s.strip() for s in self.skills.split(",") if s.strip()]
        return []




# ==========================
# Project Management Module
# ==========================
class SystemStats(models.Model):
    total_investment = models.DecimalField(max_digits=15, decimal_places=2, default=0)

    def __str__(self):
        return f"Total Investment: ₹{self.total_investment}"


class Project(models.Model):
    # Project type choices
    PROJECT_TYPE_CHOICES = [
        ("web", "Web Application"),
        ("mobile", "Mobile Application"),
        ("data", "Data Science"),
        ("cyber", "Cybersecurity"),
        ("ui", "UI/UX Design"),
    ]

    # Status choices
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("on_hold", "On Hold"),
    ]

    # Basic info
    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="projects"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    required_skills = models.TextField(help_text="Comma-separated skills", blank=True)

    # Budgets
    estimated_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    predicted_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)  # 👈 Important
    actual_budget = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    def save(self, *args, **kwargs):
        # Auto-set predicted_budget if not filled
        if not self.predicted_budget:
            self.predicted_budget = self.estimated_budget
        super().save(*args, **kwargs)     

    # Progress
    progress_percent = models.FloatField(default=0, null=True, blank=True)
    estimated_hours = models.PositiveIntegerField(null=True, blank=True)

    # Team & timeline
    team_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="assigned_projects",
        blank=True
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.get_project_type_display()})"


# ✅ Auto update SystemStats when Project created/updated/deleted
@receiver([post_save, post_delete], sender=Project)
def update_total_investment(sender, instance, **kwargs):
    stats, _ = SystemStats.objects.get_or_create(id=1)
    total = Project.objects.aggregate(total_budget=Sum("predicted_budget"))["total_budget"] or 0
    stats.total_investment = total
    stats.save()
    
# ==========================
# Notification Module
# ==========================
class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name="notifications"
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:30]}"

class Activity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.description}"

class ProjectMessage(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]}"

        
class ProgressUpdate(models.Model):
    project = models.ForeignKey("Project", on_delete=models.CASCADE, related_name="progress_updates")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    progress_percent = models.FloatField()
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.project.title} - {self.progress_percent}% by {self.user.username}"

class ProjectEarnings(models.Model):
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='project_earnings')
    freelancer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('project', 'freelancer')  # Prevent duplicate entries per project
