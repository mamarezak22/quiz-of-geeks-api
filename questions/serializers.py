from rest_framework import serializers

from questions.models import Category, Question, Answer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class AnswerSerializer(serializers.ModelSerializer):
    answer_text = serializers.CharField(source = "text")
    id = serializers.IntegerField(read_only=True)
    class Meta:
        model = Answer
        fields = ("id","answer_text")

class QuestionSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source = "text")
    answers = AnswerSerializer(many = True)
    class Meta:
        model = Question
        fields = ("question_text","answers")