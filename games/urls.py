from django.urls import path

from games.views import StartGameView, GameListView, SelectCategoryView, AnswerQuestionView,GameDetailView

urlpatterns = [
    path("games/",GameListView.as_view(),name="game-list"),
    path("games/<str:game_id>/",GameDetailView.as_view(),name="game-detail"),
    path("game/start/",StartGameView.as_view(),name="start-game"),
    path("game/<str:game_id>/select-category/",SelectCategoryView.as_view(),name="select-category"),
    path("game/<str:game_id>/answer/",AnswerQuestionView.as_view(),name="answer-question"),
]