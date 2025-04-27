from django.urls import path

urlpatterns = [
    path("game/start"),
    path("game/all"),
    path("game/<str:game_id>/start/round"),
    path("game/<str:game_id>/answer"),
]