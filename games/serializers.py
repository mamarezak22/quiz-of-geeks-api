from rest_framework import serializers

from games.models import Game


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ["id","current_round","user1_point","user2_point","created_at","ended_at","user1",
                  "user2","current_user_turn","last_turn_time"]