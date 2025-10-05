# project_management/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from authentication.views import ProjectSubmissionView, TeacherDashboardView, StudentDashboardView, AIChatbotView, AIVivaView, AIVivaEvaluationView, ProjectArchiveView, AnalyticsView, LeaderboardView, AlumniPortalView ,AllProjectsView
from authentication.views import AdminDashboardView
from authentication.views import  AppointedTeacherDashboard, UnappointedTeacherDashboard
from authentication.views import ProgressUpdateView


urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
    path('projects/submit/', ProjectSubmissionView.as_view(), name='project-submit'),

    # New URLs for the teacher dashboard
    path('teacher/submissions/', TeacherDashboardView.as_view(), name='teacher-submissions'),
    path('teacher/submissions/<int:submission_id>/', TeacherDashboardView.as_view(), name='teacher-submission-detail'),

    # New URL for the student dashboard
    path('student/submissions/', StudentDashboardView.as_view(), name='student-submissions'),
    
    # New URL for the AI chatbot
    path('ai/chat/', AIChatbotView.as_view(), name='ai-chat'),
    path('ai/viva/', AIVivaView.as_view(), name='ai-viva'),
    path('ai/viva/evaluate/', AIVivaEvaluationView.as_view(), name='ai-viva-evaluate'),
    path('projects/archive/<int:project_id>/', ProjectArchiveView.as_view(), name='project-archive'),
    path('analytics/', AnalyticsView.as_view(), name='analytics'),
    path('leaderboard/', LeaderboardView.as_view(), name='leaderboard'),
    path('alumni/my-projects/', AlumniPortalView.as_view(), name='alumni-my-projects'),
    path('projects/all/', AllProjectsView.as_view(), name='projects-all'),
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin-dashboard'),
    path('teacher/appointed/', AppointedTeacherDashboard.as_view(), name='teacher-appointed-submissions'),
    path('teacher/unappointed/', UnappointedTeacherDashboard.as_view(), name='teacher-unappointed-submissions'),
    path('projects/submit/', ProjectSubmissionView.as_view(), name='project-submit'),
    path('projects/progress/update/<int:project_id>/', ProgressUpdateView.as_view(), name='project-progress-update'),


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
