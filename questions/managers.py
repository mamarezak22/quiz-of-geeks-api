from games import models


class QuestionManager(models.Manager):
    def for_category(self,category):
        return self.filter(category=category)