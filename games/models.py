from django.db import models
import uuid

from questions.models import Category, Question
from users.models import User

class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user1 = models.ForeignKey(User, on_delete=models.SET_NULL,null = True,blank = True,related_name="game_as_user_1")
    user2 = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,blank = True,related_name="game_as_user_2")
    current_round = models.PositiveSmallIntegerField(default=0)
    user1_point = models.PositiveSmallIntegerField(default=0)
    user2_point = models.PositiveSmallIntegerField(default=0)
    shown_categories = models.ManyToManyField(Category)
    current_user_turn = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,blank = True)
    last_turn_time = models.DateTimeField(default=None, null=True,blank = True)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True)


    def __str__(self):
        return f'{self.user1} vs. {self.user2}'

class Round(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE,related_name='rounds')
    round_number = models.PositiveSmallIntegerField(default = None,null=True,blank = True)
    selected_category = models.ForeignKey(Category, on_delete=models.SET_NULL,null=True,blank = True)
    questions = models.ManyToManyField(Question,through = "QuestionRound")
    count_of_answered_question_by_user1 = models.PositiveSmallIntegerField(default = 0)
    count_of_answered_question_by_user2 = models.PositiveSmallIntegerField(default = 0)
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at  = models.DateTimeField(null=True)

class QuestionRound(models.Model):
    round = models.ForeignKey(Round, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    question_number = models.PositiveSmallIntegerField()
    is_user1_answered = models.BooleanField(default=False)
    is_user2_answered = models.BooleanField(default=False)
    user1_seen_time = models.DateTimeField(null = True,blank = True)
    user2_seen_time = models.DateTimeField(null = True,blank = True)