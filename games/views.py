from rest_framework.response import Response
from rest_framework.views import APIView
from games.services.game_logic import start_game
from .serializers import GameSerializer

class StartGameView(APIView):
    def post(self, request):
        game = start_game(request.user)
        serializer = GameSerializer(game)
        return Response(serializer.data,
                        status = 200)

