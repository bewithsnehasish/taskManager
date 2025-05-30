# tasks/serializers.py
from projects.models import Project
from rest_framework import serializers

from .models import Attachment, Comment, Task


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.CharField(
        source="assigned_to.get_full_name", read_only=True
    )
    created_by_name = serializers.CharField(
        source="created_by.get_full_name", read_only=True
    )
    project_name = serializers.CharField(source="project.name", read_only=True)

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ("created_by", "created_at", "updated_at")


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model = Comment
        fields = "__all__"
        read_only_fields = ("author", "created_at")


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = "__all__"
        read_only_fields = ("uploaded_by", "uploaded_at")
