from django.contrib import admin

from .models import CustomUser


class CustomUserAdmin(admin.ModelAdmin):
    # Define fieldsets for the admin form layout
    fieldsets = (
        (
            None,
            {"fields": ("username", "email", "first_name", "last_name", "password")},
        ),
        ("Additional Info", {"fields": ("authToken",)}),
        ("Important Dates", {"fields": ("created_at",)}),
    )

    # Fields to display in the list view
    list_display = ("username", "email", "first_name", "last_name", "created_at")

    # Fields to filter by in the admin panel
    list_filter = ("created_at",)  # Must be a tuple or list

    # Fields to search through in the admin panel
    search_fields = ("username", "email", "first_name", "last_name")

    # Default ordering of records
    ordering = ("email",)

    # Make certain fields read-only if needed
    readonly_fields = ("authToken", "created_at")


# Unregister the model if already registered to avoid conflicts
if admin.site.is_registered(CustomUser):
    admin.site.unregister(CustomUser)

# Register the model with the custom admin class
admin.site.register(CustomUser, CustomUserAdmin)
