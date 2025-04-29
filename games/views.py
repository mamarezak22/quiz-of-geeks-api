from Tools.scripts.summarize_stats import calc_execution_count_table

from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from games.services import GameService
from .permissions import IsPlayerOfGame
from .models import Game, Round, RoundQuestion
from .serializers import GameSerializer
from questions.models import Category, Question, Answer
from questions.serializers import CategorySerializer, QuestionSerializer

game_service = GameService()


#game/start
class StartGameView(APIView):
    """
    starts game for user unless user has open games as limit.
    """

    def post(self, request):
        if game_service.count_of_open_games_for_user(request.user) >= 5:
            return Response({"detail": "can not make games more than 5"},
                            status=400)
        game = game_service.get_available_game_and_join_as_user2(request.user)
        if game:
            serializer = GameSerializer(game)
            resp_text = "joined to game"
        else:
            game = Game.objects.create(user1=request.user)
            serializer = GameSerializer(game)
            resp_text = "start a new game"

        return Response({"status": resp_text,
                         "game": serializer.data},
                        status=200)


class GameListView(APIView):
    def get(self, request):
        games = game_service.get_all_open_games_for_user(request.user)
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data,
                        status=200)


#game/{game_id}/select
class SelectCategoryView(APIView):
    permission_classes = (IsPlayerOfGame,)

    def get(self, request, game_id):
        game = game_service.get_open_game_if_its_user_turn_or_404(request.user, game_id)
        self.check_object_permissions(request, game)

        current_round = game_service.get_or_create_current_round(game)
        if game_service.has_any_answered_questions(current_round):
            return Response({"detail": "the round started and can not select category for it now"},
                            status=400)

        #for the time that get for getting categories been called again.
        if len(game.shown_categories.all()) > game.current_round * 2:
            categories = game.shown_categories.all().order_by("id")[:-2]
            serializer = CategorySerializer(categories, many=True)

        else:
            categories = game_service.get_two_unused_categories_and_set_for_game(game)
            serializer = CategorySerializer(categories, many=True)

        cache.set(key=f"{game.pk} category",
                  value=[cat.id for cat in categories],
                  timeout=300)
        return Response(serializer.data,
                        status=200)

    def post(self, request, game_id):
        game = game_service.get_open_game_if_its_user_turn_or_404(request.user, game_id)
        self.check_object_permissions(request, game)
        category_ids = cache.get(f"{game.pk} category")
        if not category_ids:
            return Response({"detail": "categories been expired please get them again"},
                            status=400)
        #because we want the integer type and not string type.
        selected_category_id = int(request.data.get("selected_category_id"))
        if selected_category_id not in category_ids:
            return Response({"detail": "invalid category_id"},
                            status=400)
        selected_category_obj = Category.objects.get(pk=selected_category_id)
        game_service.setup_questions_for_current_round_of_game_with_category(game, selected_category_obj)
        return Response({"detail": f"category {selected_category_obj.name} been selected"},
                        status=200)


class AnswerQuestionView(APIView):
    permission_classes = (IsPlayerOfGame,)

    def get(self, request, game_id):
        game = game_service.get_open_game_if_its_user_turn_or_404(request.user, game_id)
        self.check_object_permissions(request, game)


        current_question_round = game_service.get_current_round_question(game)
        serializer = QuestionSerializer(current_question_round.question)

        #setted up the user1_seen_time or user2_seen_time field of roundquestion model in timezone.now()
        game_service.setup_user_seen_time_for_question(game , request.user)

        cache.set(key=f"{game.pk} question",
                  value=current_question_round.pk,
                  timeout=25)
        return Response(serializer.data,
                        status=200)

    def post(self, request, game_id):
        game = game_service.get_open_game_if_its_user_turn_or_404(request.user, game_id)
        round_question_id = cache.get(f"{game.pk} question")
        answer_id = request.data.get("answer")
        question_round = RoundQuestion.objects.get(pk=round_question_id)
        if round_question_id is None :
            return Response({"detail": "first get the question"},
                            status=400)
        if question_round.pk != round_question_id:
            return Response({"detail" : "question round expired"},
                            status = 400)

        if game_service.question_answered_before_by_user(question_round,request.user):
            return Response({"detail": "the question already answered"},
                            status=400)
        round_question_obj = RoundQuestion.objects.get(pk=round_question_id)
        question = round_question_obj.question
        answer_obj = get_object_or_404(Answer, question = question ,pk=answer_id)


        is_time_for_this_question_passed =  game_service.is_time_for_this_question_for_user_passed(question_round,request.user)
        if is_time_for_this_question_passed:
            resp_text = "time been ended for this question"
        else:
            if answer_obj.is_correct:
                resp_text = "correct answer"
            else:
                resp_text = "incorrect answer"

        game_service.handle_all_thing_for_answered_question(request.user,game , answer_obj)
        return Response({"detail": resp_text},
                        status=200)

