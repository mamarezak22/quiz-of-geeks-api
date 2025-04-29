import random
from uuid import uuid4
from datetime import timedelta

from django.db.models import QuerySet, Q
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404
from questions.models import Category,Question,Answer
from users.models import User
from games.models import Game,Round,RoundQuestion

class GameService:
    @staticmethod
    def get_all_open_games_for_user(user : User)->QuerySet[Game]:
        #find all the games that our user is in it and not ended yet and it is available.
        games = Game.objects.filter((Q(user1 = user) | Q(user2 = user)) & Q(ended_at__isnull=True))
        return games

    @staticmethod
    def count_of_open_games_for_user(user : User)->int:
        games = GameService.get_all_open_games_for_user(user)
        if games:
            return games.count()
        else:
            return 0

    @staticmethod
    def get_available_game_and_join_as_user2(user : User)->Game|None:
        with transaction.atomic():
            #all the games that have one user to be filled and user1 is not our user (the user did not join to it's game).
            game = Game.objects.filter(Q(user2__isnull=True) & ~Q(user1 = user)).select_for_update(skip_locked=True).first()
            if game:
                game.user2 = user
                game.save()
                return game
            return None

    @staticmethod
    def get_two_unused_categories_and_set_for_game(game)->QuerySet[Category]:
        """
        returns two unused category and set them for game.shown_categories too.
        """
        all_categories = Category.objects.all()
        shown_categories = game.shown_categories.all()
        not_shown_categories = [cat for cat in all_categories if cat not in shown_categories]
        two_random_category = random.sample(not_shown_categories,2)
        game.shown_categories.add(*two_random_category)
        game.save()
        return two_random_category


    @staticmethod
    def get_open_game_if_its_user_turn_or_404(user : User,game_id : uuid4)->Game|None:
        game = get_object_or_404(Game,pk = game_id,ended_at__isnull=True,current_user_turn = user)
        return game if game else None

    @staticmethod
    def get_or_create_current_round(game : Game)->Round:
        if game.current_round == 0:
            round = Round.objects.create(game = game,round_number = 1)
            game.current_round = 1
            game.save()
        else:
            round = Round.objects.get(game = game,round_number = game.current_round)
        return round

    @staticmethod
    def has_any_answered_questions(round : Round)->bool:
        return round.count_of_answered_question_by_user1 > 0 or round.count_of_answered_question_by_user2 > 0

    @staticmethod
    def setup_questions_for_current_round_of_game_with_category(game : Game,category : Category)->None:
        current_round = GameService.get_or_create_current_round(game)
        current_round.selected_category = category
        current_round.save()

        random_questions_from_category = Question.objects.for_category(current_round.selected_category).order_by("?")[:3]
        current_round.questions.set(random_questions_from_category)
        current_round.save()
        random_questions_from_category_list = list(random_questions_from_category)

        for i,question in enumerate(random_questions_from_category_list):
            RoundQuestion.objects.create(round = current_round,
                                         question = question,
                                         question_number = i+1)

    @staticmethod
    def get_current_round_question(game : Game) -> RoundQuestion:
        current_round = GameService.get_or_create_current_round(game)
        if game.current_user_turn == game.user1:
            return RoundQuestion.objects.get(round=current_round,
                                             question_number=current_round.count_of_answered_question_by_user1 + 1)
        return RoundQuestion.objects.get(round=current_round,
                                         question_number=current_round.count_of_answered_question_by_user2+1)

    @staticmethod
    def all_questions_of_this_round_answered_by_user(game : Game,user : User)->bool:
        current_round = GameService.get_or_create_current_round(game)
        if user == game.user1:
            return current_round.count_of_answered_question_by_user1>=3
        return current_round.count_of_answered_question_by_user2>=3

    @staticmethod
    def setup_user_seen_time_for_question(game : Game,user : User)->None:
        current_round_question = GameService.get_current_round_question(game)
        if user == game.user1:
            current_round_question.user1_seen_time = timezone.now()
        else:
            current_round_question.user2_seen_time = timezone.now()

    @staticmethod
    def question_answered_before_by_user(round_question : RoundQuestion,user : User)->bool:
        #if user that been called this function is user1.
        if user == round_question.round.game.user1 == user:
            if round_question.is_user1_answered:
                return True
        else:
            if round_question.is_user2_answered:
                return True
        return False

    @staticmethod
    def is_time_for_this_question_for_user_passed(round_question : RoundQuestion,user : User)->bool:
        if user == round_question.round.game.user1 == user:
            if round_question.user1_seen_time - timezone.now() > timedelta(seconds = 20):
                return True
        else:
            if round_question.user2_seen_time - timezone.now() > timedelta(seconds = 20):
                return True
        return False

    @staticmethod
    def handle_ended_round_if_round_ended(game : Game)->None:
        current_round = GameService.get_or_create_current_round(game)
        if current_round.count_of_answered_question_by_user2 == 3 and current_round.count_of_answered_question_by_user1 == 3:
            current_round = GameService.get_or_create_current_round(game)
            GameService.change_turn(game)
            current_round.ended_at = timezone.now()
            game.current_round += 1
            game.save()

    @staticmethod
    def handle_ended_game_if_game_ended(game: Game) -> None:
        round = GameService.get_or_create_current_round(game)
        if round.round_number == 5 and round.count_of_answered_question_by_user1 == 3 and round.count_of_answered_question_by_user2 == 3:
            game.ended_at = timezone.now()


    @staticmethod
    def change_turn(game : Game)->None:
        if game.user1 == game.current_user_turn:
            game.current_user_turn = game.user2
        else:
            game.current_user_turn = game.user1
        game.last_turn_time = timezone.now()
        game.save()

    @staticmethod
    def handle_database_stuff_for_answered_question(user : User,game : Game,answer : Answer):
        current_round = GameService.get_or_create_current_round(game)
        current_round_question = GameService.get_current_round_question(game)
        if user == game.user1:
            if answer.is_correct:
                game.user1_point += 1
            current_round.count_of_answered_question_by_user1 += 1
            current_round_question.is_user1_answered = True
        else:
            if answer.is_correct:
                game.user2_point += 1
            current_round_question.is_user2_answered = True
            current_round.count_of_answered_question_by_user2 += 1

    @staticmethod
    def handle_all_thing_for_answered_question(user : User,game : Game,answer : Answer) -> None:
        """
        handle all the logic after that a question been answered.
        logical database stuff and handle if round been ended and game been ended too.
        """
        GameService.handle_database_stuff_for_answered_question(user,game,answer)
        GameService.handle_ended_round_if_round_ended(game)
        GameService.handle_ended_game_if_game_ended(game)