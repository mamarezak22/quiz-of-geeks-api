from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from games.services import GameService
from games.validators import validate_uuid_param
from .permissions import IsPlayerOfGame
from .models import Game
from .serializers import GameSerializer
from questions.models import Category, Answer
from questions.serializers import CategorySerializer, QuestionSerializer

game_service = GameService()


class GameListView(APIView):
    """
        get all running games of user
    """
    def get(self, request):
        games = game_service.get_all_open_games_for_user(request.user)
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data,
                        status=200)

class GameDetailView(APIView):

    @validate_uuid_param("game_id")
    def get(self, request, game_id):
        game = get_object_or_404(Game, pk=game_id)
        serializer = GameSerializer(game)
        return Response(serializer.data,
                        status = 200)

#game/start
class StartGameView(APIView):
     def post(self, request):
        if game_service.count_of_open_games_for_user(request.user) >= 5:
            return Response({"status": "can not make games more than 5"},
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


class SelectCategoryView(APIView):
    @validate_uuid_param("game_id")
    def get(self, request, game_id):
        game = game_service.get_open_game_if_its_user_turn_or_404(request.user, game_id)

        if game_service.current_round_of_game_has_any_answered_questions(game):
            return Response({"detail": "the round started and can not select category for it now"},
                            status=400)

        #for the time that get for getting categories been called again.
        if before_categories := game_service.give_categories_that_been_created_before(game):
           categories = before_categories
           serializer = CategorySerializer(before_categories, many=True)
        else:
            categories = game_service.get_two_unused_categories_and_set_for_game(game)
            serializer = CategorySerializer(categories, many=True)
        current_round = game_service.get_or_create_current_round(game)
        cache.set(key=f"{current_round} categories",
                  value=[cat.id for cat in categories],
                  timeout=300)

        return Response(serializer.data,
                        status=200)

    @validate_uuid_param("game_id")
    def post(self, request, game_id):
        game = game_service.get_open_game_if_its_user_turn_or_404(request.user, game_id)
        current_round = game_service.get_or_create_current_round(game)

        category_ids = cache.get(f"{current_round} categories")
        if not category_ids:
            return Response({"detail": "categories been expired please get them again"},
                            status=400)
        #because we want the integer type and not string type.
        selected_category_id = int(request.data.get("category_id"))
        if selected_category_id not in category_ids:
            return Response({"detail": "invalid category_id"},
                            status=400)
        selected_category_obj = Category.objects.get(pk=selected_category_id)
        game_service.setup_questions_for_current_round_of_game_with_category(game, selected_category_obj)

        return Response({"detail": f"category {selected_category_obj.name} been selected"},
                        status=200)

class AnswerQuestionView(APIView):
    @validate_uuid_param("game_id")
    def get(self, request, game_id):
        game = game_service.get_open_game_if_its_user_turn_or_404(request.user, game_id)
        self.check_object_permissions(request, game)

        if game_service.not_selected_category_for_current_round(game):
            return Response({"detail" : "not yet seleted category for this round of game"},
                            status = 400)


        #this method validate if user seen time for current question of game been setted or not .
        #if setted means once this api called and user can not get question again.
        if game_service.question_getted_before_by_user(game,request.user):
            return Response({"detail" : "already getted question before"},
                            status = 400)

        current_question = game_service.get_current_round_question(game)
        cache.set(key=f"{game} current question",
                  value=current_question,
                  timeout=25)
        game_service.setup_user_seen_time_for_question(game , request.user)
        serializer = QuestionSerializer(current_question.question)
        return Response(serializer.data,
                        status=200)

    def post(self, request, game_id):
        game = game_service.get_open_game_if_its_user_turn_or_404(request.user, game_id)
        current_question = cache.get(f"{game} current question")
        real_current_question = game_service.get_current_round_question(game)
        answer_id = request.data.get("answer_id")
        if current_question is None :
            return Response({"detail": "first get the question"},
                            status=400)
        if current_question !=  real_current_question :
            return Response({"detail" : "question round expired"},
                            status = 400)

        if game_service.current_question_of_game_been_answered_before_by_user(game,request.user):
            return Response({"detail": "the question already answered"},
                            status=400)

        question = current_question.question
        answer_obj = get_object_or_404(Answer, question = question ,pk=answer_id)


        if game_service.is_time_for_current_question_of_game_for_this_user_passed(game,request.user):
            resp_text = "time been ended for this question"
        else:
            if answer_obj.is_correct:
                resp_text = "correct answer"
            else:
                resp_text = "incorrect answer"

        game_service.handle_all_thing_for_answered_question(user = request.user,
                                                            game = game,
                                                            answer = answer_obj)
        return Response({"detail": resp_text},
                        status=200)

