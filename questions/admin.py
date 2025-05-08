from django.contrib import admin

from questions.models import Category, Question,Answer

admin.site.register(Category)

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ['text',"is_correct"]

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
   inlines = [AnswerInline]
