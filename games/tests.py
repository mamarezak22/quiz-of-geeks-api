import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from users.models import User
from games.models import Game

@pytest.fixture
def user_factory():
    def create_user(username , phone_number , password = "12345678"):
        return User.objects.create_user(username = username, phone_number = phone_number, password = password)
    return create_user

@pytest.mark.django_db
def test_create_a_game_when_there_is_no_available_game(user_factory):
    client = APIClient()
    user1 = user_factory(username = "mohammadreza",
                         phone_number = "09161234567")
    url = reverse("start-game")
    client.force_authenticate(user=user1)
    resp = client.post(url)
    assert Game.objects.count() == 1
    game = Game.objects.first()
    assert resp.status_code == 200
    assert game.user1 == user1
    assert game.user2 is None


@pytest.mark.django_db
def test_join_a_game_when_there_is_one_available_game(user_factory):
    client = APIClient()
    user1 = user_factory(username = "mohammadreza",
                         phone_number="09161234567")
    user2 = user_factory(username = "mohammadreza1",
                         phone_number="09567899431")
    url = reverse("start-game")
    game = Game.objects.create(user1 = user1)
    client.force_authenticate(user=user2)
    resp = client.post(url)
    game.refresh_from_db() #we need refresh because the object change does not appear in test.
    assert resp.status_code == 200
    assert game.user1 == user1
    assert game.user2 == user2

@pytest.mark.django_db
def test_if_user_has_limit_game_does_not_start(user_factory):
    client = APIClient()
    user1 = user_factory(username = "mohammadreza",
                         phone_number= "0912345678")
    for i in range(5):
        Game.objects.create(user1 = user1)

    url = reverse("start-game")
    client.force_authenticate(user=user1)
    resp = client.post(url)
    assert resp.status_code == 400