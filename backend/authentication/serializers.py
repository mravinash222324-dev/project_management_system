# authentication/serializers.py
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from .models import User, ProjectSubmission, Group, Project, Team
from django.db.models import JSONField


# User serializers
class UserCreateSerializer(BaseUserCreateSerializer):
    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email', 'password', 'role')

class UserSerializer(BaseUserSerializer):
    class Meta(BaseUserSerializer.Meta):
        model = User
        fields = ('id', 'username', 'email', 'role') # 'role' field must be here
        read_only_fields = ('role',)

# Main Project Submission serializer
class ProjectSubmissionSerializer(serializers.ModelSerializer):
    # This serializer is used for both students and teachers
    student = UserSerializer(read_only=True)
    group = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all())

    class Meta:
        model = ProjectSubmission
        fields = ('id', 'student', 'title', 'abstract_text', 'abstract_file', 'audio_file', 'transcribed_text', 'submitted_at', 'group','embedding', # This field is important for Plagiarism Check
            'relevance_score', # Missing field
            'feasibility_score', # Missing field
            'innovation_score','status')
        read_only_fields = ('student', 'submitted_at', 'transcribed_text')
    def create(self, validated_data):
        # 1. Pop the custom, calculated fields that are passed by the view's serializer.save()
        embedding = validated_data.pop('embedding', None)
        relevance_score = validated_data.pop('relevance_score', 0.0)
        feasibility_score = validated_data.pop('feasibility_score', 0.0)
        innovation_score = validated_data.pop('innovation_score', 0.0)
        
        # 2. Create the instance with all remaining fields
        instance = ProjectSubmission.objects.create(**validated_data)
        
        # 3. Manually assign the popped fields to the instance
        instance.embedding = embedding
        instance.relevance_score = relevance_score
        instance.feasibility_score = feasibility_score
        instance.innovation_score = innovation_score
        
        instance.save()
        return instance

# Serializer for the teacher dashboard (read-only)
class TeacherSubmissionSerializer(serializers.ModelSerializer):
    student = UserSerializer(read_only=True)
    group_name = serializers.CharField(source='group.name', read_only=True) # NEW FIELD

    class Meta:
        model = ProjectSubmission
        fields = ('id', 'student', 'group', 'group_name', 'title', 'abstract_text', 
                  'relevance_score', 'feasibility_score', 'innovation_score', 'status')
        read_only_fields = ('id', 'student', 'group', 'group_name', 'status')
        
class ProjectSerializer(serializers.ModelSerializer):
    submission = ProjectSubmissionSerializer(read_only=True)
    team = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Project
        fields = ('id', 'title', 'abstract', 'category', 'status', 'final_report', 'submission', 'team')
        read_only_fields = ('submission', 'team')
class GroupSerializer(serializers.ModelSerializer):
    teachers = UserSerializer(many=True, read_only=True)
    students = UserSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ('id', 'name', 'description', 'teachers', 'students')

class SimilarProjectSerializer(serializers.Serializer):
    """
    A simple serializer for returning details about a similar project.
    """
    title = serializers.CharField()
    student = serializers.CharField()
    abstract_text = serializers.CharField()
class ApprovedProjectSerializer(serializers.ModelSerializer):
    """
    Serializer for the teacher's view of approved and in-progress projects.
    """
    student_name = serializers.CharField(source='submission.student.username', read_only=True)
    submission_id = serializers.IntegerField(source='submission.id', read_only=True)

    class Meta:
        model = Project
        fields = (
            'id', 
            'submission_id',
            'title', 
            'student_name', 
            'status', 
            'progress_percentage', 
            'category'
        )
class StudentSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for the student's dashboard, including project progress.
    """
    group_name = serializers.CharField(source='group.name', read_only=True)
    # This is the key addition: get progress from the related Project model
    progress = serializers.IntegerField(source='project.progress_percentage', read_only=True, allow_null=True)

    class Meta:
        model = ProjectSubmission
        fields = (
            'id', 
            'group_name', 
            'title', 
            'status', 
            'progress' # <-- The missing field is now included
        )