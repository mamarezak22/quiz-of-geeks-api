import random
from django.db.models import QuerySet, Q
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from constants import MAX_LIMIT_GAMES,COUNT_OF_QUESTION_PER_ROUND
from games.views import game_service
from questions.models import Category,Question
from users.models import User
from games.models import Game,Round,QuestionRound

class GameService:
    @staticmethod
    def find_all_available_games(user : User)->QuerySet[Game]:
        #find all the games that our user is in it and not ended yet and it is available.
        games = Game.objects.filter((Q(user1 = user) | Q(user2 = user)) & Q(ended_at__isnull=True))
        return games

    @staticmethod
    def count_of_available_games(user : User)->int:
        games = GameService.find_all_available_games(user)
        if games:
            return games.count()
        else:
            return 0

    @staticmethod
    def get_available_game(user : User)->Game|None:
        with transaction.atomic():
            #all the games that have one user to be filled and user1 is not our user (the user did not join to it's game).
            game = Game.objects.filter(Q(user2__isnull=True) & ~Q(user1 = user)).select_for_update(skip_locked=True).first()
            if game:
                game.user2 = user
                game.save()
                return game
            return None

    @staticmethod
    def start_game(user: User) -> Game|None:
        # Check if the user has reached the limit
        count = GameService.count_of_available_games(user)
        print(count)
        if GameService.count_of_available_games(user) >= MAX_LIMIT_GAMES:
            print(f"User {user.username} has reached the maximum game limit.")
            return None

        # Try to find an available game
        if game := GameService.get_available_game(user):
            print(f"User {user.username} joined an existing game.")
            return game

        # If no available game, create a new one
        print(f"Creating a new game for {user.username}.")
        game = Game.objects.create(user1=user)
        return game


    @staticmethod
    def get_two_unused_categories_and_set_for_game(game)->QuerySet[Category]:
        '''
        returns two unused category and set them for game.shown_categories too.
        '''
        all_categories = Category.objects.all()
        shown_categories = game.shown_categories.all()
        not_shown_categories = [cat for cat in all_categories if cat not in shown_categories]
        two_random_category = random.sample(not_shown_categories,2)
        game.add(*two_random_category)
        game.save()
        return two_random_category

    @staticmethod
    def is_user1(game,user:User)->bool:
        return game.user1 == user

    @staticmethod
    def get_or_create_current_round(game : Game)->Round:
        if game.current_round == 0:
            round = Round.objects.create(game = game,round_number = 1)
        else:
            round = Round.objects.get(game = game,round_number = game.current_round)
        return round

    @staticmethod
    def has_any_answered_questions(round : Round)->bool:
        return round.count_of_answered_question_by_user1 > 0 or round.count_of_answered_question_by_user2 > 0

    @staticmethod
    def get_current_round(game : Game)->Round|None:
        if game.current_round <= 0:
            return None
        else:
            return Round.objects.get(game = game,round_number = game.current_round)

    @staticmethod
    def setup_questions_for_a_round(round : Round)->None:
        random_questions_from_category = Question.objects.for_category(round.selected_category)
        round.questions.set(random_questions_from_category)
        round.save()
        random_questions_from_category_list = list(random_questions_from_category)
        for i,question in enumerate(random_questions_from_category_list):
            QuestionRound.objects.create(round = round,
                                         question = question,
                                         question_number = i+1)

    @staticmethod
    def get_current_question_round(round : Round)->QuestionRound:
        game = round.game
        if game.current_user_turn == game.user1:
            return QuestionRound.objects.get(round = round,
                                             question_number = game.current_round.count_of_answered_question_by_user1+1)
        return QuestionRound.objects.get(round = round,
                                           question_number = game.current_round.count_of_answered_question_by_user2+1)

    @staticmethod
    def is_round_ended(round : Round)->bool:
        return round.count_of_answered_question_by_user2 == 3 and round.count_of_answered_question_by_user1 == 3

    @staticmethod
    def change_turn(game : Game)->None:
        if game.user1 == game.current_user_turn:
            game.current_user_turn = game.user2
        else:
            game.current_user_turn = game.user1
        game.last_turn_time = timezone.now()
        game.save()

    @staticmethod
    def handle_ended_round(round : Round)->None:
        game = round.game
        current_round = game_service.get_current_round(game)
        game_service.change_turn(game)
        game.current_round += 1
        game.save()

    @staticmethod
    def is_game_ended(game : Game)->bool:
        if game.current_round == 5:
            if game_service.is_round_ended(game):
                return True
        return False
