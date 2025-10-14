# authentication/views.py

from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from .models import ProjectSubmission, Project, Team, User, Group
from .serializers import ProjectSubmissionSerializer, TeacherSubmissionSerializer, UserSerializer
from project_management.project_analyzer import ProjectAnalyzer
from .permissions import IsTeacherOrAdmin
from django.utils import timezone
from rest_framework import generics
from django.db.models import Count, Sum
from .serializers import ProjectSerializer
from .serializers import GroupSerializer
from django.db.models import Q
import re
from .models import Project
from rest_framework import views
from rest_framework.permissions import AllowAny
from .serializers import SimilarProjectSerializer
from .serializers import ApprovedProjectSerializer ,StudentSubmissionSerializer

analyzer = ProjectAnalyzer()
class ProjectSubmissionView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser,)

    def post(self, request, *args, **kwargs):
        # --- 1. & 2. AUTHENTICATION & GROUP CHECK ---
        user = request.user
        if user.is_anonymous:
             return Response({"error": "User must be logged in."}, status=status.HTTP_401_UNAUTHORIZED)
        
        student_groups = list(user.student_groups.all())
        if not student_groups:
            return Response({"error": "You must be a member of a group to submit a project."}, status=status.HTTP_400_BAD_REQUEST)
        
        group = student_groups[0]

        # --- 3. DATA RETRIEVAL & CLEANUP ---
        abstract_text = request.data.get('abstract_text', '').strip()
        title = request.data.get('title', '').strip()
        abstract_file = request.FILES.get('abstract_file')
        audio_file = request.FILES.get('audio_file')
        
        data = {
            'title': title,
            'abstract_text': abstract_text,
            'abstract_file': abstract_file,
            'audio_file': audio_file,
            'group': group.id,
            'relevance_score': 0.0, 'feasibility_score': 0.0, 'innovation_score': 0.0,
        }
        
        # --- 4. FILE/AUDIO PROCESSING ---
        transcribed_text = None
        if audio_file:
            transcribed_text = "Transcription successful." # Placeholder
        if transcribed_text:
            data['abstract_text'] = transcribed_text

        # --- 5. INITIAL VALIDATION & SERIALIZER ---
        serializer = ProjectSubmissionSerializer(data=data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # --- 6. AI PRE-SCREENING LOGIC ---
        text_to_analyze = data['abstract_text'] or data['title']
        new_embedding = analyzer.get_embedding(text_to_analyze)
        # Retrieve all existing ABSTRACT TEXT (not embeddings)
        existing_submissions = ProjectSubmission.objects.filter(
            ~Q(status='Rejected')
        ).values('abstract_text', 'title', 'student__username')
        
        archived_abstracts = [s['abstract_text'] for s in existing_submissions if s['abstract_text']]
        
        
        # Get AI Scores, Suggestions, and Final Report
        # The analyzer now handles the similarity check internally based on text
        analysis_result = analyzer.check_plagiarism_and_suggest_features(
            title=title,
            abstract=abstract_text,
            existing_submissions=list(existing_submissions)
        )
        
        # --- 7. FINAL DECISION (The Guaranteed Gatekeeper) ---
        if analysis_result['originality_status'] == "BLOCKED_HIGH_SIMILARITY":
            similar_project_data = {}
            if analysis_result['most_similar_project']:
                similar_project_data = SimilarProjectSerializer(analysis_result['most_similar_project']).data

            return Response({
                "detail": "Submission Blocked: High Similarity Detected. Please revise your idea.",
                "suggestions": analysis_result['full_report'],
                "similar_project": similar_project_data # <-- NEW: Send the similar project data
            }, status=status.HTTP_409_CONFLICT)
        
        # --- 8. SAVE TO DB ---
        new_embedding = analyzer.get_embedding(text_to_analyze)
        serializer.save(
            student=user,
            embedding=new_embedding,
            relevance_score=analysis_result['relevance'],
            feasibility_score=analysis_result['feasibility'],
            innovation_score=analysis_result['innovation'],
            transcribed_text=transcribed_text
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
# authentication/views.py
# ... (all existing imports and classes)

class TeacherDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

    def get(self, request, *args, **kwargs):
        """
        Returns a list of all project submissions for a teacher.
        Teachers can see all projects but will only be able to approve/reject
        projects from groups they are assigned to.
        """
        submissions = ProjectSubmission.objects.all().order_by('-submitted_at')
        serializer = TeacherSubmissionSerializer(submissions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, submission_id, *args, **kwargs):
        """Allows a teacher to approve or reject a project submission."""
        try:
            submission = ProjectSubmission.objects.get(id=submission_id)
        except ProjectSubmission.DoesNotExist:
            return Response({"detail": "Submission not found."}, status=status.HTTP_404_NOT_FOUND)

        # Check if the teacher is assigned to the project's group
        teacher_groups = request.user.teaching_groups.all()
        if submission.group not in teacher_groups:
            return Response({"detail": "You do not have permission to review this project."}, status=status.HTTP_403_FORBIDDEN)

        new_status = request.data.get('status')
        if new_status not in ['Approved', 'Rejected']:
            return Response({"detail": "Invalid status. Must be 'Approved' or 'Rejected'."}, status=status.HTTP_400_BAD_REQUEST)

        if submission.status != 'Submitted':
            return Response({"detail": "This project has already been reviewed."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the submission's status
        submission.status = new_status
        submission.save()

        # If the project is approved, create a new Project and Team
        if new_status == 'Approved':
            project = Project.objects.create(
                submission=submission,
                title=submission.title,
                abstract=submission.abstract_text,
                status='In Progress'
            )
            team = Team.objects.create(project=project)
            team.members.add(submission.student)

        serializer = TeacherSubmissionSerializer(submission)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class StudentDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """Returns a list of project submissions for the authenticated student."""
        submissions = ProjectSubmission.objects.filter(student=request.user).order_by('-submitted_at')
        # Use the new, correct serializer
        serializer = StudentSubmissionSerializer(submissions, many=True) 
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class AIChatbotView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser,) # Add JSONParser here

    def post(self, request, *args, **kwargs):
        # Check for either a text prompt or an audio file
        user_prompt = request.data.get('prompt')
        audio_file = request.data.get('audio_file')

        if not user_prompt and not audio_file:
            return Response({"error": "Prompt or audio file not provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        # If an audio file is provided, transcribe it first
        if audio_file:
            user_prompt = analyzer.transcribe_audio(audio_file.temporary_file_path())
            if not user_prompt:
                return Response({"error": "Failed to transcribe audio."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # We can also pass a project ID to provide additional context
        # TODO: Implement context fetching logic
        
        conversation_history = ""
        ai_response = analyzer.get_chat_response(user_prompt, conversation_history)
        
        return Response({"response": ai_response}, status=status.HTTP_200_OK)
    
class AIVivaView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        project_id = request.data.get('project_id')
        
        if not project_id:
            return Response({"error": "Project ID not provided."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            submission = ProjectSubmission.objects.get(id=project_id)
            # Fetch the associated Project instance to get progress
            project = Project.objects.get(submission=submission)
            progress = project.progress_percentage
        except ProjectSubmission.DoesNotExist:
            return Response({"error": "Submission not found."}, status=status.HTTP_404_NOT_FOUND)
        except Project.DoesNotExist:
            # Handle case where submission is not yet approved and has no Project model
            progress = 0 
        
        # Generate the questions using the AI service
        questions = analyzer.generate_viva_questions(
            title=submission.title,
            abstract=submission.abstract_text,
            progress_percentage=progress # <-- Passing the progress
        )
        
        return Response({"questions": questions}, status=status.HTTP_200_OK)
class AIVivaEvaluationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        project_id = request.data.get('project_id')
        question = request.data.get('question')
        answer = request.data.get('answer')
        
        if not all([project_id, question, answer]):
            return Response({"error": "Project ID, question, and answer are required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            project = ProjectSubmission.objects.get(id=project_id)
        except ProjectSubmission.DoesNotExist:
            return Response({"error": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
            
        # Evaluate the answer using the AI service
        evaluation_result = analyzer.evaluate_viva_answer(
            question=question,
            answer=answer,
            abstract=project.abstract_text
        )
        
        return Response(evaluation_result, status=status.HTTP_200_OK)

class ProjectArchiveView(APIView):
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

    def patch(self, request, project_id, *args, **kwargs):
        """Allows a teacher/admin to mark a project as completed or archived."""
        try:
            project = Project.objects.get(id=project_id)
        except Project.DoesNotExist:
            return Response({"detail": "Project not found."}, status=status.HTTP_404_NOT_FOUND)
        
        new_status = request.data.get('status')
        if new_status not in ['Completed', 'Archived']:
            return Response({"detail": "Invalid status. Must be 'Completed' or 'Archived'."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Logic for state transitions
        if new_status == 'Completed':
            if project.status == 'In Progress':
                project.status = 'Completed'
                project.end_date = timezone.now()
                project.save()
            else:
                return Response({"detail": "Project must be 'In Progress' to be marked as 'Completed'."}, status=status.HTTP_400_BAD_REQUEST)

        elif new_status == 'Archived':
            if project.status == 'Completed':
                project.status = 'Archived'
                # Optionally, here you could trigger AI report generation or other final tasks
                project.save()
            else:
                return Response({"detail": "Project must be 'Completed' to be archived."}, status=status.HTTP_400_BAD_REQUEST)

        # Update the original submission's status to reflect the project's progress
        submission = project.submission
        submission.status = new_status
        submission.save()

        return Response({"detail": f"Project status updated to {new_status}."}, status=status.HTTP_200_OK)
class AnalyticsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

    def get_queryset(self):
        # We'll return analytics data, not the models directly
        return None

    def list(self, request, *args, **kwargs):
        # Count projects by status
        status_counts = Project.objects.values('status').annotate(count=Count('status'))

        # Count projects by category
        category_counts = Project.objects.values('category').annotate(count=Count('category'))

        # Get top 5 most innovative projects (example)
        top_innovative = Project.objects.filter(status='Completed').order_by('-submission__innovation_score')[:5]
        
        top_innovative_data = [
            {'title': p.title, 'score': p.submission.innovation_score} for p in top_innovative
        ]

        data = {
            'project_status_counts': list(status_counts),
            'project_category_counts': list(category_counts),
            'top_innovative_projects': top_innovative_data,
        }
        return Response(data, status=status.HTTP_200_OK)
class LeaderboardView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_queryset(self):
        # FIX: We annotate ALL users with their total innovation score (using a left join)
        # Then, we filter out users with no projects (or where the score is NULL/0)
        
        # 1. Annotate all users with a score (NULL if no projects)
        queryset = User.objects.annotate(
            total_innovation=Sum(
                'active_projects__project__submission__innovation_score'
            )
        )
        
        # 2. Filter out users who have no score (i.e., no completed projects) 
        # and sort by score, taking the top 10.
        return queryset.filter(
            total_innovation__isnull=False,
            active_projects__project__status='Completed' # Only count COMPLETED projects
        ).order_by('-total_innovation')[:10]

    # ... (list method remains the same)

class AlumniPortalView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSubmissionSerializer # Display full details of the submission

    def get_queryset(self):
        # FIX: Ensure we fetch only the student's own submissions with final statuses
        return ProjectSubmission.objects.filter(
            student=self.request.user,
            status__in=['Completed', 'Archived'] # Checks the status field in ProjectSubmission
        ).order_by('-submitted_at')
    
    
class AllProjectsView(generics.ListAPIView):
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer # Corrected serializer

class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]

    def get(self, request, *args, **kwargs):
        users = User.objects.all()
        groups = Group.objects.all()

        user_serializer = UserSerializer(users, many=True)
        group_serializer = GroupSerializer(groups, many=True)

        return Response({
            'users': user_serializer.data,
            'groups': group_serializer.data,
        }, status=status.HTTP_200_OK)

    def patch(self, request, group_id, *args, **kwargs):
        # We will add logic here to update the group members later
        return Response({"detail": "Group update not implemented yet."}, status=status.HTTP_200_OK)
class AppointedTeacherDashboard(generics.ListAPIView):
    """
    Dashboard 1: Projects from groups the teacher is assigned to.
    Allows approval/rejection actions (PATCH).
    """
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    serializer_class = TeacherSubmissionSerializer

    def get_queryset(self):
        # Get all groups the logged-in teacher is part of
        teacher_groups = self.request.user.teaching_groups.all()
        
        # Filter submissions that belong to any of these groups and are still 'Submitted'
        return ProjectSubmission.objects.filter(
            group__in=teacher_groups,
            status='Submitted'
        ).order_by('-submitted_at')

class UnappointedTeacherDashboard(generics.ListAPIView):
    """
    Dashboard 2: Projects from all other groups. Read-only view.
    """
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    serializer_class = TeacherSubmissionSerializer

    def get_queryset(self):
        # Get all groups the logged-in teacher is part of
        teacher_groups = self.request.user.teaching_groups.all()
        
        # Filter submissions that DO NOT belong to the teacher's groups
        # The teacher can view all submissions, regardless of status, if they are not in the group.
        return ProjectSubmission.objects.filter(
            ~Q(group__in=teacher_groups)
        ).order_by('-submitted_at')
class ProjectProgressView(views.APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, project_id, *args, **kwargs):
        try:
            # FIX: We must try to get a Project instance first
            project = Project.objects.get(submission__id=project_id) 
            return Response({"progress_percentage": project.progress_percentage}, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
             # Handle cases where the Project doesn't exist yet (not approved)
            return Response({"progress_percentage": 0}, status=status.HTTP_200_OK)
class ProgressUpdateView(views.APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, submission_id, *args, **kwargs): # <-- FIX IS HERE: submission_id added
        user = request.user
        new_progress = request.data.get('progress')
        
        # 1. Validation Checks
        if new_progress is None or not isinstance(new_progress, int):
            return Response({"error": "Progress value (integer) is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not 0 <= new_progress <= 100:
            return Response({"error": "Progress must be between 0 and 100."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 2. Find the Project via the Submission ID
            submission = ProjectSubmission.objects.get(id=submission_id)
            project = Project.objects.get(submission=submission) # Get the linked Project instance
        except ProjectSubmission.DoesNotExist:
            return Response({"error": "Submission not found."}, status=status.HTTP_404_NOT_FOUND)
        except Project.DoesNotExist:
             return Response({"error": "Project has not been approved yet. Cannot update progress."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Ownership Check
        if project.submission.student != user:
            return Response({"error": "You do not own this project."}, status=status.HTTP_403_FORBIDDEN)

        # 4. Update and Save
        project.progress_percentage = new_progress
        project.save()

        return Response({"detail": f"Progress updated to {new_progress}%"}, status=status.HTTP_200_OK)
class TopAlumniProjectsView(generics.ListAPIView):
    """
    A public view to showcase the top 10 best-rated alumni projects.
    """
    permission_classes = [AllowAny]  # <-- This makes the endpoint public
    serializer_class = ProjectSubmissionSerializer

    def get_queryset(self):
        # Fetches projects that are completed or archived
        # Orders them by innovation, then relevance, then feasibility score
        # Limits the result to the top 10
        return ProjectSubmission.objects.filter(
            status__in=['Completed', 'Archived']
        ).order_by(
            '-innovation_score', 
            '-relevance_score', 
            '-feasibility_score'
        )[:10]
    
class ApprovedProjectsView(generics.ListAPIView):
    """
    Provides a list of all projects that are 'In Progress' or 'Completed'
    for the teacher dashboard.
    """
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    serializer_class = ApprovedProjectSerializer

    def get_queryset(self):
        # Fetches all projects that are past the submission stage
        return Project.objects.filter(
            status__in=['In Progress', 'Completed', 'Archived']
        ).order_by('-submission__submitted_at')
