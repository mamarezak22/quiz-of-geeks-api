from django.db import models

from questions.managers import QuestionManager


class Category(models.Model):
    name = models.CharField(max_length=100)
    def __str__(self):
        return self.name

class Question(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE,related_name="questions")
    text = models.TextField()

    objects = QuestionManager()

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE,related_name="answers")
    text = models.TextField()
    is_correct = models.BooleanField(default=False)
