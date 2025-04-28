from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from games.services import  GameService
from .permissions import IsPlayerOfGame
from .models import Game,Round,QuestionRound
from .serializers import GameSerializer
from questions.models import Category, Question, Answer
from questions.serializers import CategorySerializer,QuestionSerializer

game_service = GameService()

class StartGameView(APIView):
    """
    starts game for user unless user has open games as limit.
    """
    def post(self, request):
        game = game_service.start_game(request.user)
        if game:
            serializer = GameSerializer(game)
            return Response(serializer.data,
                            status = 200)
        return Response({"detail" : "can not make games more than 5"},
                        status = 400)

class GameListView(APIView):
    def get(self, request):
        games = game_service.find_all_available_games(request.user)
        serializer = GameSerializer(games, many=True)
        return Response(serializer.data,
                        status=200)

class SelectCategoryView(APIView):
    permission_classes = (IsPlayerOfGame,)
    def get(self,request,game_id):
        game = get_object_or_404(Game,pk=game_id,current_user_turn = request.user,ended_at__isnull = True)
        self.check_object_permissions(request,game)
        current_round = game_service.get_or_create_current_round(game)
        if game_service.has_any_answered_questions(current_round):
            return Response({"detail" : "the round started and can not select category for it now"},
                            status = 400)

        #for the time that get for getting categories been called again.
        if len(game.shown_categories.all()) > game.current_round * 2:
            serializer = CategorySerializer(game.shown_categories.all().order_by('id')[:-2],many=True)
            cache.set(key = game.pk,
                      value = [cat.id for cat in serializer.data],
                      timeout = 300)
            return Response(serializer.data,
                            status = 200)

        categories = game_service.get_two_unused_categories_and_set_for_game(game)

        cache.set(key = game.pk,
                  value = [cat.id for cat in categories],
                  timeout = 300)
        serializer = CategorySerializer(categories,many=True)
        return Response(serializer.data,
                        status = 200)

    def post(self, request,game_id):
        game = get_object_or_404(Game, pk=game_id, current_user_turn=request.user, ended_at__isnull=True)
        self.check_object_permissions(request,game)
        category_ids = cache.get(game.pk)
        if not category_ids:
            return Response({"detail" : "categories been expired please get them again"},
                            status = 400)
        #because we want the integer type and not string type.
        selected_category_id = int(request.data.get("selected_category_id"))
        if selected_category_id not in category_ids:
            return Response({"detail" : "invalid category_id"},
                            status = 400)
        selected_category_obj = Category.objects.get(pk=selected_category_id)
        current_round = game_service.get_or_create_current_round(game)
        current_round.selected_category = selected_category_obj
        current_round.save()
        game_service.setup_questions_for_a_round(current_round)
        return Response({"detail" : f"category {selected_category_obj.name} been selected"},
                        status = 200)


class AnswerQuestionView(APIView):
    permission_classes = (IsPlayerOfGame,)
    def get(self,request,game_id):
        game  = get_object_or_404(Game,pk = game_id, current_user_turn = request.user, ended_at__isnull=True)
        self.check_object_permissions(request,game)
        current_round = game_service.get_or_create_current_round(game)
        current_question_round = game_service.get_current_question_round(current_round)
        if current_question_round.question_number > 3:
            return Response({"detail" : "all questions been answered"},
                            status = 400)

        serializer = QuestionSerializer(current_question_round.question)
        if game_service.is_user1(game,request.user):
            current_question_round.user1_seen_time = timezone.now()
        current_question_round.user2_seen_time = timezone.now()
        cache.set(key=game_id,
                  value = current_question_round.pk,
                  timeout = 25)
        return Response(serializer.data,
                        status = 200)

    def post(self,request,game_id):
        question_round_id = cache.get(game_id)
        answer_text = request.data.get("answer")
        if question_round_id is None:
            return Response({"detail" : "first get the question"},
                            status = 400)
        last_question_of_round = False
        game = Game.objects.get(pk=game_id)
        current_round = game_service.get_or_create_current_round(game)
        question_round = QuestionRound.objects.get(pk=question_round_id)
        is_user1 = game_service.is_user1(game,request.user)
        answer_obj = get_object_or_404(Answer, text=answer_text)

        correct = answer_obj.is_correct

        if is_user1:
            if question_round.is_answered_question_by_user1:
                return Response({"detail" : "question been answered already"},
                                status = 400)
            if not timezone.now() - question_round.user1_seen_time < timedelta(seconds=20):
                resp_text = "time for this question ended"

            else:
                if correct:
                    game.user1_point += 1
            current_round.count_of_answered_question_by_user1 += 1
            question_round.is_answered_question_by_user1 = True

        else:
            if question_round.is_answered_question_by_user2:
                return Response({"detail" : "question been answered already"},
                                status = 400)
            if not timezone.now() - question_round.user2_seen_time <= timedelta(seconds=20):
                resp_text = "time for this question ended"
            else:
                if correct:
                    game.user2_point += 1
            current_round.count_of_answered_question_by_user2 += 1
            question_round.is_answered_question_by_user2 = True

        if correct:
            resp_text = "correct answer"
        else:
            resp_text = "wrong answer"

        if game_service.is_round_ended(current_round):
            game_service.handle_ended_round(current_round)
        if game_service.is_game_ended(game):
            game.ended_at = timezone.now()
        return Response({"detail": resp_text}, status=200)