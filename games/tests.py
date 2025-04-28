import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from questions.serializers import CategorySerializer
from users.models import User
from games.models import Game
from questions.models import Question,Category

@pytest.fixture
def user1():
    return User.objects.create_user(username='user1', password='11111111',phone_number = "09123456780")

@pytest.fixture
def user2():
    return User.objects.create_user(username='user2', password='22222222',phone_number="09123456789")


@pytest.fixture
def create_categories():
    names = [
        "هوش مصنوعی و علم داده",
        "بک اند",
        "فرانت اند",
        "برنامه نویسی موبایل",
        "اطلاعات عمومی",
        "شبکه و امنیت",
        "بازی سازی",
        "الگوریتم و ساختمان داده ها",
        "سخت افزار",
        "سیستم دیزاین",
    ]
    categories = [Category.objects.create(name=name) for name in names]
    return categories

@pytest.mark.django_db
def test_create_a_game_when_there_is_no_available_game(user1):
    client = APIClient()
    url = reverse("start-game")
    client.force_authenticate(user=user1)
    resp = client.post(url)
    assert Game.objects.count() == 1
    game = Game.objects.first()
    assert resp.status_code == 200
    assert game.user1 == user1
    assert game.user2 is None


@pytest.mark.django_db
def test_join_a_game_when_there_is_one_available_game(user1,user2):
    client = APIClient()
    url = reverse("start-game")
    game = Game.objects.create(user1 = user1)
    client.force_authenticate(user=user2)
    resp = client.post(url)
    game.refresh_from_db() #we need refresh because the object change does not appear in test.
    assert resp.status_code == 200
    assert game.user1 == user1
    assert game.user2 == user2

@pytest.mark.django_db
def test_if_user_has_limit_game_does_not_start(user1):
    client = APIClient()
    for i in range(5):
        Game.objects.create(user1 = user1)

    url = reverse("start-game")
    client.force_authenticate(user=user1)
    resp = client.post(url)
    assert resp.status_code == 400

@pytest.mark.django_db
def test_get_categories_for_first_round_if_user_not_its_turn(user1,user2):
    client = APIClient()
    client.force_authenticate(user = user2)
    game = Game.objects.create(user1 = user1,user2 = user2,current_user_turn = user1)
    select_category_url = reverse("select-category",kwargs={"game_id":game.pk})
    resp = client.get(select_category_url)
    #game not founded that its turn was user2
    assert resp.status_code == 404

@pytest.mark.django_db
def test_get_categories_for_first_round_if_user_it_is_turn(user1,user2,create_categories):
    client = APIClient()
    game = Game.objects.create(user1 = user1,user2 = user2,current_user_turn = user1)
    client.force_authenticate(user = user1)
    select_category_url = reverse("select-category",kwargs={"game_id":game.pk})
    resp = client.get(select_category_url)
    data = resp.json()
    assert resp.status_code == 200
    assert len(data) == 2
    assert all('id' in category and 'name' in category for category in data)

@pytest.mark.django_db
def test_set_category_for_first_round(user1,user2,create_categories):
    client = APIClient()
    game = Game.objects.create(user1=user1, user2=user2, current_user_turn=user1)
    client.force_authenticate(user=user1)
    select_category_url = reverse("select-category", kwargs={"game_id": game.pk})
    resp = client.get(select_category_url)
    data = resp.json()
    to_be_selected = data[0]["id"]
    select_category_url = reverse("select-category", kwargs={"game_id": game.pk})
    resp = client.post(select_category_url, data = {"selected_category_id":to_be_selected})
    print(resp.json())
    assert resp.status_code == 200
#
# @pytest.mark.django_db
# def test_answer_question_if_is_turn(user1,user2,create_categories):
#     client = APIClient()
#     game = Game.objects.create(user1 = user1,user2 = user2,current_user_turn = user1)
#
#
