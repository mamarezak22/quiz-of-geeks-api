import random
from uuid import UUID, uuid4
from datetime import timedelta

from django.db.models import QuerySet, Q
from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404

from games.enums import Result
from questions.models import Category,Question,Answer
from users.models import User, UserHistory
from games.models import Game,Round,RoundQuestion

class GameService:
    @staticmethod
    def get_all_open_games_for_user(user : User)->QuerySet[Game]:
        #find all the games that our user is in it and not ended yet and it is available.
        games = Game.objects.filter((Q(user1 = user) | Q(user2 = user)) & Q(ended_at__isnull=True))
        return games

    @staticmethod
    def count_of_open_games_for_user(user : User)->int:
        #if there is no game count method returns 0 and handle this case.
        return GameService.get_all_open_games_for_user(user).count()

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
    def give_categories_that_been_created_before(game : Game) -> list[Category]|None:
        #this condition happens when we are in round 1 and 2 categories been showned.
        #or round 2 and 4 category been showed.
        #so we show the user last shown categories again.
        if game.shown_categories.all().count() == game.current_round_number * 2:
            categories = game.shown_categories.all().order_by("id")
            categories = categories[len(categories) - 2:]
            return categories

    @staticmethod
    def get_two_unused_categories_and_set_for_game(game)->list[Category]:
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
    def get_open_game_if_its_user_turn_or_404(user : User,game_id : UUID)->Game|None:
        game = get_object_or_404(Game,pk = game_id,ended_at__isnull=True,current_user_turn = user)
        return game if game else None

    @staticmethod
    def get_or_create_current_round(game : Game)->Round:
        if game.current_round_number == 0:
            round = Round.objects.create(game = game,round_number = 1)
            game.current_round_number = 1
            game.save()
        else:
            try :
                round = Round.objects.get(game = game,round_number = game. current_round_number)
            except:
                round = Round.objects.create(game = game,
                                             round_number = game.current_round_number)
        return round

    @staticmethod
    def current_round_of_game_has_any_answered_questions(game : Game)->bool:
        current_round = GameService.get_or_create_current_round(game)
        return current_round.count_of_answered_question_by_user1 >= 1 or current_round.count_of_answered_question_by_user2 >=1

    @staticmethod
    def setup_questions_for_current_round_of_game_with_category(game : Game,category : Category)->None:
        current_round = GameService.get_or_create_current_round(game)
        if not current_round.selected_category:
            current_round.selected_category = category

        random_questions_from_category = Question.objects.for_category(category).order_by("?")[:3]
        if random_questions_from_category.count() < 3 :
            raise ValueError("not have questions")

        for i,question in enumerate(list(random_questions_from_category)):
            RoundQuestion.objects.create(round = current_round,
                                            question = question,
                                            question_number = i+1)
        current_round.questions.set(random_questions_from_category)
        current_round.save()

    @staticmethod
    def get_current_round_question(game : Game) -> RoundQuestion:
        current_round = GameService.get_or_create_current_round(game)
        if game.current_user_turn == game.user1:
            return RoundQuestion.objects.get(round=current_round,
                                             question_number=current_round.count_of_answered_question_by_user1 + 1)
        return RoundQuestion.objects.get(round=current_round,
                                         question_number=current_round.count_of_answered_question_by_user2+1)
    @staticmethod
    def not_selected_category_for_current_round(game : Game)-> bool:
        """
        if last round been ended but not created any new round for it in selectcategory view we dont 
        have a round with that round number so we return true. 
        """
        try :
            round = Round.objects.get(game = game,
                                      round_number = game.current_round_number)
            return False
        except:
            return True
                        
        
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

        current_round_question.save()

    @staticmethod 
    def question_getted_before_by_user(game : Game,user : User)-> bool:
        current_question_round = GameService.get_current_round_question(game)
        if user == game.user1 and current_question_round.user1_seen_time is not None:
            return True
        elif user == game.user2 and current_question_round.user2_seen_time is not None:
            return True
        return False

    @staticmethod
    def current_question_of_game_been_answered_before_by_user(game : Game,user : User)->bool:
        current_question = GameService.get_current_round_question(game)
        if user == game.user1: 
            if current_question.is_user1_answered:
                return True
        else:
            if current_question.is_user2_answered:
                return True
        return False

    @staticmethod
    def is_time_for_current_question_of_game_for_this_user_passed(game : Game,user : User)->bool:
        current_question = GameService.get_current_round_question(game)
        if user == game.user1 :
            time_answered = timezone.now() - current_question.user1_seen_time 
            if time_answered >= timedelta(seconds = 20):
                return True
        else:
            time_answered = timezone.now() - current_question.user2_seen_time 
            if time_answered >= timedelta(seconds = 20):
                return True
        return False

    @staticmethod
    def get_user_result_for_game(game : Game,user : User)->Result:
        if user == game.user1:
            if game.user1_point > game.user2_point:
                return Result.WIN
            elif game.user1_point < game.user2_point:
                return Result.LOSE
            else:
                return Result.TIE
        else:
            if game.user1_point > game.user2_point:
                return Result.LOSE
            elif game.user2_point > game.user1_point:
                return Result.WIN
            else:
                return Result.TIE

    @staticmethod
    def save_result_of_the_game_in_user_history_for_users_of_games(game : Game) -> None:
        users = [game.user1, game.user2]
        for user in users:
            user_history,_ = UserHistory.objects.get_or_create(user = user)
            if GameService.get_user_result_for_game(game,user) == Result.TIE:
                user_history.count_of_tie_games += 1
            elif GameService.get_user_result_for_game(game,user) == Result.WIN:
                user_history.count_of_win_games += 1
            else:
                user_history.count_of_lose_games += 1
            user_history.count_of_games += 1
            user_history.save()


    @staticmethod
    def handle_ended_round_if_round_ended(game : Game)->None:
        current_round = GameService.get_or_create_current_round(game)
        if current_round.count_of_answered_question_by_user2 == 3 and current_round.count_of_answered_question_by_user1 == 3:
            current_round.ended_at = timezone.now()
            if game.current_round_number == 5 :
                GameService.handle_ended_game_if_game_ended(game)
            else:
                game.current_round_number+=1 
            game.save()
            current_round.save()

    @staticmethod
    def handle_change_turn_when_a_user_answers_all_its_questions(user : User,
                                                                 game : Game):
                                                    
        """
        changes the current_turn_user of game model when a round been answered by a user and we need to change the turn
        """
        current_round = GameService.get_or_create_current_round(game)
        if user == game.user1:
            #prime rounds game been passed by user1.
           if current_round.count_of_answered_question_by_user1 == 3 and current_round.round_number%2==1:
            GameService.change_turn(game)
        else:
            #even rounds been passed by user2.
            if current_round.count_of_answered_question_by_user2 == 3 and current_round.round_number%2==0:
                GameService.change_turn(game)

    @staticmethod
    def handle_ended_game_if_game_ended(game: Game) -> None:
        #we call handle_ended_round_if_round_ended before that and that makes current_round_number == 6.
        GameService.save_result_of_the_game_in_user_history_for_users_of_games(game)
        game.ended_at = timezone.now()
        game.save()


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
            current_round_question.is_user1_answered = True 
            current_round.count_of_answered_question_by_user1 += 1
        else:
            if answer.is_correct:
                game.user2_point += 1
            current_round_question.is_user2_answered = True
            current_round.count_of_answered_question_by_user2 += 1
        game.save()
        current_round.save()
        current_round_question.save()

    @staticmethod
    def handle_all_thing_for_answered_question(user : User,game : Game,answer : Answer) -> None:
        """
        handle all the logic after that a question been answered.
        logical database stuff and handle if round been ended and game been ended too.
        """
        GameService.handle_database_stuff_for_answered_question(user,game,answer)
        GameService.handle_change_turn_when_a_user_answers_all_its_questions(user,game)
        GameService.handle_ended_round_if_round_ended(game)
