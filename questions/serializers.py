from rest_framework import serializers

from questions.models import Category, Question, Answer


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'

class AnswerSerializer(serializers.ModelSerializer):
    answer_text = serializers.CharField(source = "text")
    class Meta:
        model = Answer
        fields = ("answer_text",)

class QuestionSerializer(serializers.ModelSerializer):
    question = serializers.CharField(source = "text")
    answer = AnswerSerializer()
    class Meta:
        model = Question
        fields = ("question","answer")