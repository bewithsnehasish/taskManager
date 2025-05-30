from django.contrib import admin

from .models import Category, Comment, Task, TaskAssignment, TaskAttachment

# Register your models here.

admin.site.register(Category)
admin.site.register(Task)
admin.site.register(TaskAssignment)
admin.site.register(Comment)
admin.site.register(TaskAttachment)
