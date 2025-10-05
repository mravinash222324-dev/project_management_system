# authentication/serializers.py
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer
from djoser.serializers import UserSerializer as BaseUserSerializer
from rest_framework import serializers
from .models import User, ProjectSubmission, Group, Project, Team

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