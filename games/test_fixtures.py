import pytest
from users.models import User
from games.models import Game, Round
from questions.models import Category,Answer,Question
from django.urls import reverse

@pytest.fixture
def user1():
    return User.objects.create_user(username='user1', password='11111111', phone_number="09123456780")


@pytest.fixture
def user2():
    return User.objects.create_user(username='user2', password='22222222', phone_number="09123456789")

@pytest.fixture
def create_game():
    def _create(**kwargs):
        return Game.objects.create(**kwargs)
    return _create

@pytest.fixture
def create_round():
    def _create(**kwargs):
        return Round.objects.create(**kwargs)
    return _create

@pytest.fixture
def categories():
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
    categories = [Category.objects.create(name = name) for name in names]
    return categories

@pytest.fixture 
def create_question_and_answer_for_wanted_category():
    def _create(category: Category):
        questions = []
        for i in range(3):
            question = Question.objects.create(text=f"{i}", category=category)
            questions.append(question)
            for j in range(4):
                Answer.objects.create(
                    question=question,
                    text=f"{i}",
                    is_correct=(j == 0)
                )
        return questions
    return _create






@pytest.fixture
def start_game_url():
    return reverse("start-game")

@pytest.fixture
def select_category_url():
    """
    you give that a game_id and it creates a url with that game_id.

    > select_category_url(game_id = 2) = reverse("select-category"),kwargs = {"game_id" : 2})
    """
    return lambda game_id: reverse('select-category', kwargs={'game_id': game_id})

@pytest.fixture
def answer_question_url():
    return lambda game_id: reverse("answer-question",kwargs={"game_id" : game_id})
