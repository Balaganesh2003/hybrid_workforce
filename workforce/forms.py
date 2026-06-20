from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from .models import CustomUser, Profile, Project, ProjectMessage 


User = get_user_model()

# -------------------------
# Role Choices
# -------------------------
ROLE_CHOICES = [
    ("client", "Client"),
    ("full_time", "Full-Time"),
    ("freelancer", "Freelancer"),
]

# =========================
# Custom User Creation Form
# =========================
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "password1", "password2", "role"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.user_type = self.cleaned_data["role"]

        if commit:
            user.save()
            # Auto create Profile for freelancers & full-time users
            if user.user_type in ["freelancer", "full_time"]:
                Profile.objects.get_or_create(user=user)
        return user


# =========================
# User Update Form
# =========================
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ["username", "email"]


# =========================
# Profile Update Form
# =========================
class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = [
            "phone", "location", "bio",
            "user_type", "hourly_rate", "monthly_salary",
            "availability", "skills", "experience",
        ]
        widgets = {
            "bio": forms.Textarea(attrs={
                "rows": 4, "placeholder": "Write about yourself..."
            }),
            "skills": forms.TextInput(attrs={
                "placeholder": "e.g., Python, Django, React"
            }),
            "experience": forms.Textarea(attrs={
                "rows": 3, "placeholder": "Describe your work experience..."
            }),
            "availability": forms.Select(),
            "user_type": forms.Select(),
            "hourly_rate": forms.NumberInput(attrs={
                "placeholder": "Enter hourly rate (₹/hr)"
            }),
            "monthly_salary": forms.NumberInput(attrs={
                "placeholder": "Enter monthly salary (₹)"
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get("user_type")
        hourly_rate = cleaned_data.get("hourly_rate")
        monthly_salary = cleaned_data.get("monthly_salary")

        # Validation: ensure hourly_rate only for freelancers
        if user_type == "freelancer" and not hourly_rate:
            self.add_error("hourly_rate", "Hourly rate is required for freelancers.")

        # Validation: ensure monthly_salary only for full-time
        if user_type == "full_time" and not monthly_salary:
            self.add_error("monthly_salary", "Monthly salary is required for full-time users.")

        # Optional: hide irrelevant values
        if user_type == "freelancer":
            cleaned_data["monthly_salary"] = None
        elif user_type == "full_time":
            cleaned_data["hourly_rate"] = None

        return cleaned_data


# =========================
# Project Form (used for create/edit project)
# =========================
class ProjectForm(forms.ModelForm):
    start_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )
    end_date = forms.DateField(
        widget=forms.DateInput(attrs={"type": "date"})
    )

    class Meta:
        model = Project
        fields = [
            "title",
            "description",
            "required_skills",
            "project_type",
            "estimated_budget",
            "start_date",
            "end_date",
            "team_members",
            "status",
            "estimated_hours",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Project Title"}),
            "description": forms.Textarea(attrs={"placeholder": "Project Description"}),
            "required_skills": forms.TextInput(attrs={"placeholder": "e.g., Django, UI/UX"}),
            "estimated_budget": forms.NumberInput(attrs={"placeholder": "e.g., 50000"}),
            "project_type": forms.Select(attrs={"class": "form-control"}),  # Dropdown
            "status": forms.Select(),
            "team_members": forms.CheckboxSelectMultiple(),
        }


# =========================
# Budget Prediction Form (used only in predict_budget_view)
# =========================
class BudgetPredictionForm(forms.Form):
    PROJECT_TYPE_CHOICES = [
        ("Web Development", "Web Development"),
        ("Mobile App", "Mobile App"),
        ("Data Science", "Data Science"),
        ("UI/UX Design", "UI/UX Design"),
    ]

    total_hours = forms.DecimalField(
        label="Estimated Hours",
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={"placeholder": "e.g., 120"})
    )

    project_type = forms.ChoiceField(
        label="Project Type",
        choices=PROJECT_TYPE_CHOICES
    )

    team_size = forms.IntegerField(
        label="Team Size",
        min_value=1,
        widget=forms.NumberInput(attrs={"placeholder": "e.g., 5"})
    )

class ProjectMessageForm(forms.ModelForm):
    class Meta:
        model = ProjectMessage
        fields = ["content"]
        widgets = {
            "content": forms.Textarea(attrs={"rows": 2, "placeholder": "Type your message..."}),
        }

class ProgressForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["progress_percent"]  
        widgets = {
            "progress_percent": forms.NumberInput(attrs={"min": 0, "max": 100}),
        }

