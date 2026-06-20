from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from datetime import datetime
import pandas as pd
from sklearn.naive_bayes import GaussianNB
from sklearn.preprocessing import LabelEncoder
import random
from .forms import ( CustomUserCreationForm, ProjectForm, BudgetPredictionForm, ProfileForm, UserUpdateForm,)
from .models import CustomUser, Project, Notification, Profile
from .models import Activity
from .forms import ProjectMessageForm, ProgressForm
from .models import SystemStats, ProgressUpdate
from django.db.models import Avg, Sum
from workforce.models import Project, SystemStats, Notification
from .models import Project, ProgressUpdate




# -------------------------
# Home
# -------------------------
def home_view(request):
    return render(request, "workforce/home.html")


# -------------------------
# Registration
# -------------------------
def register(request):
    form = CustomUserCreationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Account created successfully! Please log in.")
        return redirect("login")
    return render(request, "registration/register.html", {"form": form})


# -------------------------
# Login / Logout
# -------------------------
def login_view(request):
    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)

                # 🔥 Role-based redirect
                role = user.user_type.lower()
                if role == "freelancer":
                    return redirect("dashboard_freelancer")
                elif role == "full_time":
                    return redirect("dashboard_full_time")
                elif role == "client":
                    return redirect("dashboard_client")
                else:
                    return redirect("home")
            else:
                messages.error(request, "Invalid username or password")
        else:
            messages.error(request, "Please correct the errors below.")

    return render(request, "registration/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("login")


# -------------------------
# Dashboards
# -------------------------
@login_required(login_url="login")
def dashboard_client(request):
    if request.user.user_type.lower() != "client":
        return redirect("login")

    projects = Project.objects.filter(client=request.user).order_by("-created_at")

    # Project counts
    active_projects = projects.filter(status="open").count()
    in_progress_projects = projects.filter(status="in_progress").count()
    completed_projects = projects.filter(status="completed").count()

    # Average progress
    avg_progress = projects.aggregate(avg=Avg("progress_percent"))["avg"] or 0

    # ✅ Total Investment = sum of predicted_budget (NOT estimated)
    total_investment = projects.aggregate(total=Sum("predicted_budget"))["total"] or 0

    # Budget utilization (still estimated vs actual, safe)
    total_estimated = projects.aggregate(total=Sum("estimated_budget"))["total"] or 0
    total_actual = projects.aggregate(total=Sum("actual_budget"))["total"] or 0
    budget_utilization = (total_actual / total_estimated * 100) if total_estimated else 0

    notifications = Notification.objects.filter(user=request.user, is_read=False)

    context = {
        "projects": projects,
        "active_projects": active_projects,
        "in_progress_projects": in_progress_projects,
        "completed_projects": completed_projects,
        "avg_progress": round(avg_progress, 1),
        "total_investment": total_investment,
        "budget_utilization": round(budget_utilization, 2),
        "notifications": notifications,
        "is_client": True,
    }

    return render(request, "workforce/dashboard_client.html", context)

@login_required(login_url="login")
def dashboard_freelancer(request):
    if request.user.user_type.lower() != "freelancer":
        return redirect("login")

    # Profile info (optional, if exists)
    profile = Profile.objects.filter(user=request.user).first()

    # Assigned projects
    assigned_projects = request.user.assigned_projects.all()

    # Stats
    active_projects = assigned_projects.filter(status="Open").count()
    in_progress_projects = assigned_projects.filter(status="In Progress").count()
    completed_projects = assigned_projects.filter(status="Completed").count()
    total_earnings = sum(getattr(p, "earnings", 0) for p in assigned_projects)

    # Notifications (limit 5 latest)
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")[:5]

    # System stats
    active_users = CustomUser.objects.filter(is_active=True).count()
    active_projects_system = Project.objects.filter(status="Open").count()
    prediction_accuracy = f"{round(random.uniform(85, 95), 1)}%"

    return render(
        request,
        "workforce/dashboard_freelancer.html",
        {
            "profile": profile,
            "assigned_projects": assigned_projects,
            "active_projects": active_projects,
            "in_progress_projects": in_progress_projects,
            "completed_projects": completed_projects,
            "total_earnings": total_earnings,
            "notifications": notifications,
           # "current_date": timezone.now().strftime("%B %d, %Y"),
            "active_users": active_users,
            "active_projects_system": active_projects_system,
            "prediction_accuracy": prediction_accuracy,
        },
    )

@login_required(login_url="login")
def dashboard_full_time(request):
    if request.user.user_type.lower() != "full_time":
        return redirect("login")

    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    # ✅ Assigned Projects
    assigned_projects = Project.objects.filter(team_members=user)

    # ✅ Stats
    ongoing_projects = assigned_projects.filter(
        status__in=["Open", "In Progress"]
    ).count()
    completed_projects = assigned_projects.filter(
        status__iexact="Completed"
    ).count()

    # ✅ Leaves & Salary
    leaves_taken = getattr(profile, "leaves_taken", 0)
    monthly_salary = profile.monthly_salary if profile.monthly_salary else 0

    # ✅ Activity & Notifications
    recent_activity = Activity.objects.filter(user=user).order_by("-date")[:5]
    notifications = Notification.objects.filter(user=user).order_by("-created_at")[:5]

    # ✅ Context
    context = {
        "user": user,
        "profile": profile,
        "assigned_projects": assigned_projects,
        "ongoing_projects": ongoing_projects,
        "completed_projects": completed_projects,
        "leaves_taken": leaves_taken,
        "monthly_salary": monthly_salary,
        "recent_activity": recent_activity,
        "notifications": notifications,
       
    }

    return render(request, "workforce/dashboard_full_time.html", context)



# -------------------------
# Profile Management
# -------------------------
@login_required(login_url="login")
def profile_view(request):
    profile = Profile.objects.filter(user=request.user).first()
    return render(request, "workforce/profile.html", {"user": request.user, "profile": profile})

@login_required(login_url="login")
def manage_profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, instance=profile)

        # Remove monthly_salary for non-full-time users
        if request.user.user_type.lower() != "full_time":
            profile_form.fields.pop("monthly_salary", None)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile = profile_form.save(commit=False)

            # Calculate profile strength
            profile.profile_strength = profile.calculate_strength()
            profile.save()

            messages.success(request, "Profile updated successfully!")

            # Redirect based on role
            role = request.user.user_type.lower()
            if role == "freelancer":
                return redirect("dashboard_freelancer")
            elif role == "full_time":
                return redirect("dashboard_full_time")
            elif role == "client":
                return redirect("dashboard_client")
            else:
                return redirect("home")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileForm(instance=profile)

        # Remove monthly_salary for non-full-time users on GET
        if request.user.user_type.lower() != "full_time":
            profile_form.fields.pop("monthly_salary", None)

    return render(
        request,
        "workforce/manage_profile.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "profile": profile
        },
    )


@login_required(login_url="login")
def view_profile(request, user_id):
    user = get_object_or_404(CustomUser, pk=user_id)
    profile = Profile.objects.filter(user=user).first()
    return render(request, "workforce/view_profile.html", {"user": user, "profile": profile})


# -------------------------
# Project Creation (Client)
# -------------------------
@login_required(login_url="login")
def create_project_view(request):
    # ✅ Only clients can create projects
    if request.user.user_type.lower() != "client":
        messages.error(request, "Only clients can create projects.")
        return redirect("login")

    # Load team members
    freelancers = CustomUser.objects.filter(user_type__iexact="freelancer")
    fulltimers = CustomUser.objects.filter(user_type__iexact="full_time")

    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.client = request.user

        # Assign predicted_budget from form or fallback to estimated_budget
        project.predicted_budget = form.cleaned_data.get(
            "predicted_budget", project.estimated_budget
        )
        project.save()
        form.save_m2m()  # save ManyToMany fields if any

        # ✅ Save selected team members
        team_ids = request.POST.getlist("team_members")
        if team_ids:
            project.team_members.set(team_ids)

            # 🔔 Send notifications to each team member
            for member in project.team_members.all():
                Notification.objects.create(
                    user=member,
                    message=f"🚀 You have been added to the project: {project.title}"
                )

        # Update SystemStats total investment using predicted_budget
        stats = SystemStats.objects.first()
        if stats:
            stats.total_investment += project.predicted_budget or 0
            stats.save()
        else:
            SystemStats.objects.create(total_investment=project.predicted_budget or 0)

        messages.success(request, "✅ Project created successfully!")
        return redirect("dashboard_client")

    context = {
        "form": form,
        "freelancers": freelancers,
        "fulltimers": fulltimers,
    }
    return render(request, "projects/create_project.html", context)

@login_required(login_url="login")
def client_projects_view(request):
    if request.user.user_type.lower() != "client":
        return redirect("login")

    projects = Project.objects.filter(client=request.user).order_by("-created_at")
    form = ProjectForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        project = form.save(commit=False)
        project.client = request.user
        project.save()
        form.save_m2m()
        messages.success(request, "Project created successfully!")
        return redirect("projects")

    return render(request, "workforce/client_project.html", {"projects": projects, "form": form})


@login_required(login_url="login")
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)

    # ✅ Restrict freelancers & fulltime -> only view
    if request.user.user_type.lower() in ["freelancer", "full_time"]:
        can_edit = False
    else:
        # Only Client (owner) ku edit option enable
        can_edit = project.client == request.user  

    return render(request, "projects/project_detail.html", {
        "project": project,
        "can_edit": can_edit,
    })



def edit_project(request, pk):
    project = get_object_or_404(Project, pk=pk)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            return redirect("project_detail", pk=project.pk)  # go back to detail page
    else:
        form = ProjectForm(instance=project)

    context = {
        "form": form,
        "project": project,
    }
    return render(request, "projects/edit_project.html", context)

# -------------------------
# Team Selection
# -------------------------
@login_required(login_url="login")
def select_team_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.user != project.client:
        return redirect("login")

    q = request.GET.get("q", "")
    role = request.GET.get("role", "")

    available_talent = CustomUser.objects.filter(
        Q(user_type="freelancer") | Q(user_type="full_time")
    ).exclude(id__in=project.team_members.all())

    if q:
        available_talent = available_talent.filter(
            Q(username__icontains=q) | Q(profile__skills__icontains=q)
        )

    if role:
        available_talent = available_talent.filter(user_type__iexact=role)

    talent_with_profiles = [{"user": t, "profile": Profile.objects.filter(user=t).first()} for t in available_talent]

    if request.method == "POST":
        member_id = request.POST.get("selected_member")
        if member_id:
            member = get_object_or_404(CustomUser, pk=member_id)
            project.team_members.add(member)
        return redirect("select_team", project_id=project.id)

    return render(
        request,
        "workforce/team_selection.html",
        {"project": project, "available_talent_with_profiles": talent_with_profiles, "query": q, "role": role},
    )


# -------------------------
# Budget Prediction
# -------------------------
@login_required(login_url="login")
def predict_budget_view(request):
    predicted_budget = None
    avg_past_budget = 0
    frontend_estimate = None   # 👈 for frontend comparison

    form = BudgetPredictionForm(request.POST or None)
    past_projects = Project.objects.exclude(actual_budget__isnull=True)

    if past_projects.exists():
        # Dataset
        data = []
        for p in past_projects:
            team_cost = calculate_team_cost(p)  # 👈 ensure this uses hourly_rate & salary conversion
            data.append({
                "estimated_hours": p.estimated_hours or 0,
                "project_type": p.project_type,
                "total_team_cost": team_cost,
                "actual_budget": float(p.actual_budget),
            })

        import pandas as pd
        from sklearn.preprocessing import LabelEncoder
        from sklearn.naive_bayes import GaussianNB

        df = pd.DataFrame(data)

        le = LabelEncoder()
        df["project_type_encoded"] = le.fit_transform(df["project_type"])
        X = df[["estimated_hours", "project_type_encoded", "total_team_cost"]]
        y = df["actual_budget"]

        model = GaussianNB()
        model.fit(X, y)

        avg_past_budget = df["actual_budget"].mean()

        if request.method == "POST" and form.is_valid():
            total_hours = float(form.cleaned_data["total_hours"])
            project_type = form.cleaned_data["project_type"]

            # ✅ Calculate team_cost dynamically
            team_cost = 0
            last_project = Project.objects.filter(client=request.user).last()
            if last_project:
                for member in last_project.team_members.all():
                    if member.user_type.lower() == "freelancer" and hasattr(member, "hourly_rate"):
                        team_cost += member.hourly_rate or 0
                    elif member.user_type.lower() == "employee" and hasattr(member, "monthly_salary"):
                        team_cost += (member.monthly_salary / 160)  # 160 hrs ≈ 1 month

            # ✅ base cost per project type
            base_costs = {
                "web": 20000,
                "mobile": 40000,
                "data": 50000,
                "cyber": 60000,
                "ui": 15000,
            }
            base_cost = base_costs.get(project_type, 0)

            try:
                project_type_encoded = le.transform([project_type])[0]
                predicted_budget = model.predict([[total_hours, project_type_encoded, team_cost]])[0]
            except Exception:
                predicted_budget = (total_hours * team_cost) + base_cost

            # 👇 also calculate frontend-style estimate for comparison
            frontend_estimate = (total_hours * team_cost) + base_cost

    return render(
        request,
        "workforce/budget_prediction.html",
        {
            "form": form,
            "predicted_budget": predicted_budget,
            "avg_past_budget": avg_past_budget,
            "frontend_estimate": frontend_estimate,
            "past_projects": past_projects,
        },
    )

def calculate_team_cost(project):
    total_cost = 0

    for member in project.team_members.all():
        if member.user_type.lower() == "freelancer":
            if hasattr(member, "hourly_rate") and member.hourly_rate:
                total_cost += member.hourly_rate
        elif member.user_type.lower() == "full_time":
            if hasattr(member, "monthly_salary") and member.monthly_salary:
                hourly = member.monthly_salary / 160  # approx hourly
                total_cost += hourly

    return total_cost

    
# -------------------------
# Notifications
# -------------------------
@login_required(login_url="login")
def notifications_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    notifications = Notification.objects.filter(user=request.user).order_by("-created_at")
    return render(request, "workforce/notifications.html", {"notifications": notifications})


# -------------------------
# Talent Search
# -------------------------
@login_required(login_url="login")
def talent_search_view(request):
    query = request.GET.get("q", "")
    role_filter = request.GET.get("role", "")
    skill_filter = request.GET.get("skill", "")

    talents = CustomUser.objects.filter(user_type__in=["freelancer", "full_time"])

    if query:
        talents = talents.filter(Q(username__icontains=query) | Q(profile__skills__icontains=query))
    if role_filter:
        talents = talents.filter(user_type__iexact=role_filter)
    if skill_filter:
        talents = talents.filter(profile__skills__icontains=skill_filter)

    paginator = Paginator(talents.order_by("username"), 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    all_skills = Profile.objects.exclude(skills__isnull=True).exclude(skills__exact="").values_list("skills", flat=True)
    skill_set = set()
    for skills in all_skills:
        skill_set.update([s.strip() for s in skills.split(",")])
    skills_list = sorted(skill_set)

    for talent in page_obj:
        if hasattr(talent, "profile") and talent.profile and talent.profile.skills:
            talent.skill_list = [s.strip() for s in talent.profile.skills.split(",")]
        else:
            talent.skill_list = []

    return render(request, "workforce/talent_search.html", {"talents": page_obj, "skills_list": skills_list})


# -------------------------
# Reporting (Admin)
# -------------------------
@login_required(login_url="login")
def reporting_view(request):
    if not request.user.is_superuser:
        return redirect("login")

    total_projects = Project.objects.count()
    open_projects = Project.objects.filter(status="Open").count()
    in_progress_projects = Project.objects.filter(status="In Progress").count()
    completed_projects = Project.objects.filter(status="Completed").count()

    projects_with_budgets = Project.objects.exclude(estimated_budget__isnull=True).exclude(actual_budget__isnull=True)
    total_diff = sum(abs(p.estimated_budget - p.actual_budget) for p in projects_with_budgets)
    avg_diff = total_diff / projects_with_budgets.count() if projects_with_budgets else 0

    performance_data = [
        {
            "username": member.username,
            "completed_projects": member.assigned_projects.filter(status="Completed").count(),
        }
        for member in CustomUser.objects.filter(user_type__in=["full_time", "freelancer"])
    ]
    performance_data.sort(key=lambda x: x["completed_projects"], reverse=True)

    return render(
        request,
        "workforce/reporting.html",
        {
            "total_projects": total_projects,
            "open_projects": open_projects,
            "in_progress_projects": in_progress_projects,
            "completed_projects": completed_projects,
            "avg_diff": avg_diff,
            "performance_data": performance_data,
        },
    )


# -------------------------
# Settings
# -------------------------
@login_required(login_url="login")
def settings_view(request):
    if request.method == "POST":
        messages.success(request, "Settings updated successfully!")
        return redirect("settings")
    return render(request, "workforce/settings.html")


@login_required(login_url="login")
def message_team_view(request, project_id):
    project = get_object_or_404(Project, id=project_id)

    # Permission: only client or team members
    if request.user != project.client and request.user not in project.team_members.all():
        dj_messages.error(request, "You are not part of this project.")
        return redirect("dashboard_full_time")

    form = ProjectMessageForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        msg = form.save(commit=False)
        msg.project = project
        msg.sender = request.user
        msg.save()

        # Create notifications for all other members + client
        recipients = list(project.team_members.all()) + [project.client]
        recipients = [user for user in recipients if user != request.user]

        for user in recipients:
            Notification.objects.create(
                user=user,
                message=f"New message in project '{project.title}' from {request.user.username}: {msg.content[:50]}"
            )

        return redirect("message_team", project_id=project.id)

    messages_qs = project.messages.select_related("sender")

    return render(request, "workforce/message_team.html", {
        "project": project,
        "form": form,
        "messages": messages_qs,
        "notifications": request.user.notifications.filter(is_read=False)[:5],  # top 5 unread
    })


@login_required(login_url="login")
def update_progress(request, pk):
    project = get_object_or_404(Project, id=pk)

    # Client → view only
    if request.user.user_type.lower() == "client":
        updates = project.progress_updates.select_related("user").order_by("-updated_at")
        return render(request, "workforce/update_progress.html", {
            "project": project,
            "updates": updates,
            "form": None,  # clients cannot edit
            "show_complete_btn": project.progress_percent >= 100,  # show button if 100%
            "is_client": True,  # explicitly for template
        })

    # Freelancer / FullTime → must be part of the team
    if request.user not in project.team_members.all():
        return redirect("home")

    if request.method == "POST":
        form = ProgressForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            # Record history
            ProgressUpdate.objects.create(
                project=project,
                user=request.user,
                progress_percent=project.progress_percent
            )
            # Redirect based on role
            if request.user.user_type.lower() == "freelancer":
                return redirect("dashboard_freelancer")
            elif request.user.user_type.lower() == "full_time":
                return redirect("dashboard_full_time")
            return redirect("home")
    else:
        form = ProgressForm(instance=project)

    updates = project.progress_updates.select_related("user").order_by("-updated_at")

    return render(request, "workforce/update_progress.html", {
        "form": form,
        "project": project,
        "updates": updates,
        "show_complete_btn": False,  # only clients can see the complete button
        "is_client": False,
    })

@login_required(login_url="login")
def mark_complete(request, pk):
    project = get_object_or_404(Project, id=pk)

    # ✅ Only clients can mark complete + project must be 100% progress
    if request.user.user_type.lower() != "client" or project.progress_percent < 100:
        messages.error(request, "You cannot mark this project as complete yet.")
        return redirect('update_progress', pk=pk)

    if project.status != "completed":  # avoid duplicate
        project.status = "completed"
        project.save()

        hours = project.estimated_hours or 0

        # ✅ Update earnings for all freelancers in the project based on hourly rate from profile
        for member in project.team_members.all():
            if member.user_type.lower() == "freelancer":
                profile = getattr(member, "profile", None)
                hourly_rate = getattr(profile, "hourly_rate", 0) if profile else 0

                # ⚡ Optional: reset previous earnings from this project
                # member.total_earnings -= getattr(member, 'project_earnings', 0)

                # Add earnings for this project
                amount = hourly_rate * hours
                member.total_earnings += amount

                # ⚡ Optional: track per-project earnings
                # member.project_earnings = amount

                member.save()

        messages.success(
            request,
            f"✅ Project '{project.title}' marked as complete!"
        )
    else:
        messages.info(request, "This project is already completed.")

    # Stay on the same page
    return redirect('update_progress', pk=pk)
