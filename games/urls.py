from django.urls import path

from games.views import StartGameView, GameListView, SelectCategoryView, AnswerQuestionView

urlpatterns = [
    path("game/start",StartGameView.as_view(),name="start-game"),
    path("game/all",GameListView.as_view(),name="game-list"),
    path("game/<str:game_id>/select-category",SelectCategoryView.as_view(),name="select-category"),
    path("game/<str:game_id>/answer",AnswerQuestionView.as_view(),name="answer-question"),
]