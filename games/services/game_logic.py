from django.db.models import QuerySet, Q
from django.db import transaction
from constants import MAX_LIMIT_GAMES
from users.models import User
from games.models import Game

def find_all_available_games(user : User)->QuerySet[Game]:
    #find all the games that our user is in it and not ended yet and it is available.
    games = Game.objects.filter((Q(user1 = user) | Q(user2 = user)) & Q(ended_at__isnull=True))

def count_of_available_games(user : User)->int:
    return find_all_available_games(user).count()

def get_available_game(user : User)->Game:
    with transaction.atomic():
        #all the games that have one user to be filled and user1 is not our user (the user did not join to it's game).
        game = Game.objects.filter(Q(user2__isnull=True) & ~Q(user1 = user)).select_for_update(skip_locked=True).first()
        if game:
            game.user2 = user
            game.save()
            return game
        return None

def start_game(user : User)->Game:
    if count_of_available_games(user) > MAX_LIMIT_GAMES :
        return None
    if game := get_available_game(user):
        return game

    game = Game.objects.create(user1 = user)
    return game






