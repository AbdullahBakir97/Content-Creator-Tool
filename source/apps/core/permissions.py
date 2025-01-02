from rest_framework import permissions

class IsContentCreator(permissions.BasePermission):
    """
    Custom permission to only allow approved content creators to access content.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated and is an approved content creator
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_content_creator and
            request.user.creator_status == 'approved'
        )
    
    def has_object_permission(self, request, view, obj):
        # Check if user is the creator of the content
        return obj.creator == request.user
