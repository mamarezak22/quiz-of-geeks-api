import time
import pytest
from datetime import timedelta
from rest_framework.test import APIClient
from questions.models import Answer, Category
from users.models import User
from games.models import Game,Round
from games.services import GameService
from users.models import UserHistory
from .test_fixtures import (user1,user2,create_game,create_round,create_question_and_answer_for_wanted_category,
                            start_game_url,answer_question_url,select_category_url,categories)
from django.utils import timezone

game_service = GameService()

@pytest.mark.django_db
def test_create_game_when_there_is_no_available_game(user1,start_game_url): 
    client = APIClient()
    client.force_authenticate(user=user1)
    resp = client.post(start_game_url)

    game = Game.objects.first()
    assert resp.status_code == 200
    assert game.user1 == user1
    assert game.current_user_turn == user1
    assert game.user2 is None


@pytest.mark.django_db
def test_join_game_when_one_available_game(user1, user2,create_game,start_game_url):
    client = APIClient()

    game = create_game(user1 = user1)
    # User2 joins the available game
    client.force_authenticate(user=user2)
    resp = client.post(start_game_url)

    # Validate user2 joined the game
    game.refresh_from_db()
    assert resp.status_code == 200
    assert game.user1 == user1
    assert game.user2 == user2


@pytest.mark.django_db
def test_user_game_limit(user1,start_game_url):
    client = APIClient()
    client.force_authenticate(user=user1)

    # User1 creates 5 games (should not be able to create the 6th)
    for _ in range(5):
        client.post(start_game_url)

    resp = client.post(start_game_url)
    assert resp.status_code == 400  
    assert resp.data["status"] == "can not make games more than 5"



@pytest.mark.django_db
def test_user_not_joined_to_the_game_that_its_user1_its_our_user(user1,create_game,start_game_url):
    client = APIClient()
    game = create_game(user1 = user1)

    client.force_authenticate(user = user1)

    game = Game.objects.first()

    assert game.user2 != user1  # User1 should not join as user2

    resp = client.post(start_game_url)

    assert resp.data["status"] == "start a new game"


@pytest.mark.django_db
def test_get_categories_for_first_round_if_user_not_its_turn(user1,user2,create_game,categories,select_category_url):
    client = APIClient()
    game = create_game(user1 = user1,
                       user2 = user2)
    client.force_authenticate(user = user2)
    resp = client.get(select_category_url(game.pk))
    #game not founded that its turn was user2
    assert resp.status_code == 404

@pytest.mark.django_db
def test_get_categories_for_first_round_user_it_is_turn_of_user(user1, user2,create_game ,categories, select_category_url):
    client = APIClient()
    game = create_game(user1 = user1,user2 = user2)
    client.force_authenticate(user = user1)
    
    resp = client.get(select_category_url(game.pk))
    #current_round_round_number been changed and we want examine that change.
    game.refresh_from_db()
    assert resp.status_code == 200
    assert game.current_round_number == 1
    assert len(resp.data) == 2


@pytest.mark.django_db
def test_set_category_for_first_round(user1, user2, create_game,categories,create_question_and_answer_for_wanted_category,select_category_url):
    client = APIClient()
    client.force_authenticate(user=user1)
    game = create_game(user1 = user1,user2 = user2)
    resp = client.get(select_category_url(game.pk))
    to_be_selected_category_id = resp.data[0]["id"]
    to_be_selected_category_obj = Category.objects.get(pk = to_be_selected_category_id)
    other_shown_category_obj = Category.objects.get(pk = resp.data[1]["id"])
    create_question_and_answer_for_wanted_category(to_be_selected_category_obj)
    resp = client.post(select_category_url(game.pk), data = {"category_id":to_be_selected_category_id})
    #the game current_round_number been changed so we need to update it and then get the current round.
    game.refresh_from_db()
    current_round = game_service.get_or_create_current_round(game)
    assert resp.status_code == 200
    assert current_round.selected_category == to_be_selected_category_obj
    assert current_round.questions.all().count() == 3
    shown_category_ids = [cat.id for cat in game.shown_categories.all()]
    #asserting that game.shown_categories == shown_categories in get request.
    #i use sorted because in assertion [1,5] != [5,1]
    #but sorted([1,5]) == sorted([5,1])
    assert sorted(shown_category_ids) == sorted([to_be_selected_category_id,other_shown_category_obj.id])


@pytest.mark.django_db
def test_if_select_category_been_called_again_it_shows_already_created_categories(user1, user2, create_game 
                                                                                  ,categories,select_category_url):
    client = APIClient()
    game = create_game(user1 = user1,user2 = user2)
    client.force_authenticate(user=user1)
    resp1 = client.get(select_category_url(game.pk))
    resp2 = client.get(select_category_url(game.pk))
    data1 = resp1.json()
    data2 = resp2.json()
    resp1_ids = [data1[0]["id"] , data1[1]["id"]] 
    resp2_ids = [data2[0]["id"], data2[1]["id"]]
    #we just check if cat_ids in both cases are equal.
    assert sorted(resp1_ids) == sorted(resp2_ids)

@pytest.mark.django_db
def test_answer_first_question_by_user_1_in_wrong_answer(user1,user2,create_game,categories,select_category_url,create_question_and_answer_for_wanted_category,answer_question_url):
    """
    we check all the stuff after answering a question like get resp schema
    registering seen time for user and ...
    in this test with wrong answer
    and in next test only test correct answer situation
    """
    client = APIClient()
    game = create_game(user1 = user1,
                       user2 = user2)

    client.force_authenticate(user = user1)
    #process of selecting a cateogry
    resp = client.get(select_category_url(game.pk))
    to_be_selected_category_id = resp.data[0]["id"]
    to_be_selected_category_obj = Category.objects.get(pk = to_be_selected_category_id)
    create_question_and_answer_for_wanted_category(to_be_selected_category_obj)
    client.post(select_category_url(game.pk), data = {"category_id":to_be_selected_category_id})

    get_resp = client.get(answer_question_url(game.pk))
    assert get_resp.status_code == 200
    get_resp_data = get_resp.json()
    #we select one wrong answer to be used in posting through answer_question_url.
    for answer in get_resp_data["answers"]:
        answer_obj = Answer.objects.get(pk = answer["id"])
        if not answer_obj.is_correct:
            to_be_selected_wrong_answer_id = answer["id"]
            break
    #validating json structure
    assert "question_text" in get_resp_data and isinstance(get_resp_data["question_text"], str)
    assert "answers" in get_resp_data and isinstance(get_resp_data["answers"], list)

    for answer in get_resp_data["answers"]:
        assert "id" in answer and isinstance(answer["id"], int)
        assert "answer_text" in answer and isinstance(answer["answer_text"], str)
    game.refresh_from_db() 
    current_question = game_service.get_current_round_question(game)

    #when this url get's the seen time for user been registered.
    assert current_question.user1_seen_time <= timezone.now()
    post_resp = client.post(answer_question_url(game.pk),data = {"answer_id" : to_be_selected_wrong_answer_id})
    game.refresh_from_db()
    current_round = game_service.get_or_create_current_round(game)
    assert post_resp.status_code == 200
    assert game.user1_point == 0
    current_question.refresh_from_db()
    assert current_question.is_user1_answered == True 
    assert current_round.count_of_answered_question_by_user1 == 1 

@pytest.mark.django_db
def test_answer_first_question_by_user_1_in_wrong_answer(user1,user2,create_game,categories,select_category_url,create_question_and_answer_for_wanted_category,answer_question_url):
    client = APIClient()
    game = create_game(user1 = user1,
                       user2 = user2)

    client.force_authenticate(user = user1)
    #process of selecting a cateogry
    resp = client.get(select_category_url(game.pk))
    to_be_selected_category_id = resp.data[0]["id"]
    to_be_selected_category_obj = Category.objects.get(pk = to_be_selected_category_id)
    create_question_and_answer_for_wanted_category(to_be_selected_category_obj)
    client.post(select_category_url(game.pk), data = {"category_id":to_be_selected_category_id})

    get_resp = client.get(answer_question_url(game.pk))
    get_resp_data = get_resp.json()
    #we select one wrong answer to be used in posting through answer_question_url.
    for answer in get_resp_data["answers"]:
        answer_obj = Answer.objects.get(pk = answer["id"])
        if answer_obj.is_correct:
            to_be_selected_correct_answer_id = answer["id"]
            break
    client.post(answer_question_url(game.pk), data = {"answer_id": to_be_selected_correct_answer_id})
    game.refresh_from_db()
    assert game.user1_point == 1

@pytest.mark.django_db
def test_answer_first_question_by_user_1_when_times_passed(user1,user2,create_game,categories,select_category_url,create_question_and_answer_for_wanted_category,answer_question_url,mocker):
    client = APIClient()
    game = create_game(user1 = user1,
                       user2 = user2)

    client.force_authenticate(user = user1)
    #process of selecting a cateogry
    resp = client.get(select_category_url(game.pk))
    to_be_selected_category_id = resp.data[0]["id"]
    to_be_selected_category_obj = Category.objects.get(pk = to_be_selected_category_id)
    create_question_and_answer_for_wanted_category(to_be_selected_category_obj)

    client.post(select_category_url(game.pk), data = {"category_id":to_be_selected_category_id})

    get_resp = client.get(answer_question_url(game.pk))
    get_resp_data = get_resp.data
    to_be_selected_ansewer_id = get_resp_data["answers"][0]["id"]
    game.refresh_from_db()
    current_question = game_service.get_current_round_question(game)

    #mocking that 21s been passed and now if user answer that question it time been passed.
    mocker.patch("django.utils.timezone.now", return_value=timezone.now() + timedelta(seconds=21))
    resp = client.post(answer_question_url(game.pk), data = {"answer_id": to_be_selected_ansewer_id})
    data = resp.json()
    assert resp.status_code == 200
    assert data["detail"] == "time been ended for this question"
    current_question.refresh_from_db()
    current_round = game_service.get_or_create_current_round(game)

    assert game.user1_point == 0
    assert current_question.is_user1_answered == True 
    assert current_round.count_of_answered_question_by_user1 == 1

@pytest.mark.django_db
def test_answering_3_question_by_user1_and_turn_switches_to_user2(user1,user2,create_game,categories,select_category_url,create_question_and_answer_for_wanted_category,answer_question_url):
    client = APIClient()
    game = create_game(user1 = user1,
                       user2 = user2)

    client.force_authenticate(user = user1)
    #process of selecting a cateogry
    resp = client.get(select_category_url(game.pk))
    to_be_selected_category_id = resp.data[0]["id"]
    to_be_selected_category_obj = Category.objects.get(pk = to_be_selected_category_id)
    create_question_and_answer_for_wanted_category(to_be_selected_category_obj)

    client.post(select_category_url(game.pk), data = {"category_id":to_be_selected_category_id})

    for _ in range(3):
        get_resp = client.get(answer_question_url(game.pk))
        get_resp_data = get_resp.data
        to_be_selected_ansewer_id = get_resp_data["answers"][0]["id"]
        resp = client.post(answer_question_url(game.pk), data = {"answer_id": to_be_selected_ansewer_id})
    game.refresh_from_db()
    assert game.current_user_turn == user2
    #there is some miliseconds that need to be considered. 
    assert timezone.now() - game.last_turn_time <= timedelta(seconds = 1) 

@pytest.mark.django_db
def test_changing_round_when_round_ends(user1,user2,create_game,categories,select_category_url,create_question_and_answer_for_wanted_category,answer_question_url):
    client = APIClient()
    game = create_game(user1 = user1,
                       user2 = user2)

    client.force_authenticate(user = user1)
    #process of selecting a cateogry
    resp = client.get(select_category_url(game.pk))
    to_be_selected_category_id = resp.data[0]["id"]
    to_be_selected_category_obj = Category.objects.get(pk = to_be_selected_category_id)
    create_question_and_answer_for_wanted_category(to_be_selected_category_obj)

    client.post(select_category_url(game.pk), data = {"category_id":to_be_selected_category_id})

    for _ in range(3):
        get_resp = client.get(answer_question_url(game.pk))
        get_resp_data = get_resp.data
        to_be_selected_ansewer_id = get_resp_data["answers"][0]["id"]
        resp = client.post(answer_question_url(game.pk), data = {"answer_id": to_be_selected_ansewer_id})

    for _ in range(3):
        client.force_authenticate(user = user2)
        get_resp = client.get(answer_question_url(game.pk))
        get_resp_data = get_resp.data
        to_be_selected_ansewer_id = get_resp_data["answers"][0]["id"]
        resp = client.post(answer_question_url(game.pk), data = {"answer_id": to_be_selected_ansewer_id})

    game.refresh_from_db()
    assert game.current_round_number == 2
    first_round = Round.objects.get(game = game,
                                    round_number = 1)
    assert timezone.now() - first_round.ended_at <= timedelta(seconds = 1)

@pytest.mark.django_db
def test_ending_game_and_saving_all_things_to_history(user1,user2,create_game,categories,select_category_url,create_question_and_answer_for_wanted_category,answer_question_url):
    client = APIClient()
    game = create_game(user1 = user1,
                       user2 = user2)

    #process of selecting a cateogry
    ROUND_COUNTS = 5
    QUESTION_COUNTS = 3
    for i in range(ROUND_COUNTS):
        game.refresh_from_db()
        if game.current_user_turn == user1:
            client.force_authenticate(user = user1)
        else:
            client.force_authenticate(user = user2)
        resp = client.get(select_category_url(game.pk))
        to_be_selected_category_id = resp.data[0]["id"]
        to_be_selected_category_obj = Category.objects.get(pk = to_be_selected_category_id)
        create_question_and_answer_for_wanted_category(to_be_selected_category_obj)

        client.post(select_category_url(game.pk), data = {"category_id":to_be_selected_category_id})
        print(f"category {to_be_selected_category_obj} been setted for {i+1} round by user{game.current_user_turn.pk}")
        print()
    #we have 2 sides that must answer questions in each round.
        for _ in range(2):
            for _ in range(QUESTION_COUNTS):
                game.refresh_from_db()
                current_question = game_service.get_current_round_question(game)
                if game.current_user_turn == user1:
                    client.force_authenticate(user = user1) 
                else:
                    client.force_authenticate(user = user2)
                get_resp = client.get(answer_question_url(game.pk))
                get_resp_data = get_resp.data
                for answer in get_resp_data["answers"]:
                    answer_obj = Answer.objects.get(pk = answer["id"])
    
                    if answer_obj.is_correct:
                        to_be_selected_correct_answer_id = answer["id"]
                        break
                resp = client.post(answer_question_url(game.pk), data = {"answer_id": to_be_selected_correct_answer_id})
                print(f"question {current_question.question_number} been answered by {game.current_user_turn.pk}")
    game.refresh_from_db()
    assert game.current_round_number == 5
    assert timezone.now() - game.ended_at <= timedelta(seconds = 1)
    assert game.user1_point == 15
    assert game.user2_point == 15
    assert game.shown_categories.all().count() == 10
    users_of_games = [game.user1, game.user2]
    for user in users_of_games:
        history =  UserHistory.objects.get(user = user)
        assert history.count_of_tie_games == 1
        assert history.count_of_games == 1 

@pytest.mark.django_db
def test_can_not_select_category_if_round_started_before(user1,user2,create_game,
                                                         categories,create_question_and_answer_for_wanted_category,
                                                         select_category_url,answer_question_url):
    client = APIClient()
    game = create_game(user1 = user1,user2 = user2)
    client.force_authenticate(user = user1)
    resp = client.get(select_category_url(game.pk))
    to_be_selected_category_id = resp.data[0]["id"]
    to_be_selected_category_obj = Category.objects.get(pk = to_be_selected_category_id)
    create_question_and_answer_for_wanted_category(to_be_selected_category_obj)

#ansering one question of round
    client.post(select_category_url(game.pk), data = {"category_id":to_be_selected_category_id})
    get_resp = client.get(answer_question_url(game.pk))
    get_resp_data = get_resp.data
    to_be_selected_answer_id = get_resp_data["answers"][0]["id"]
    resp = client.post(answer_question_url(game.pk), data = {"answer_id": to_be_selected_answer_id})

    resp = client.get(select_category_url(game.pk))
    assert resp.data["detail"] == "the round started and can not select category for it now"
    assert resp.status_code == 400
