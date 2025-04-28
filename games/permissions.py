from rest_framework.permissions import BasePermission

class IsPlayerOfGame(BasePermission):
    def has_object_permission(self, request, view,object):
        return request.user in [object.user1,object.user2]