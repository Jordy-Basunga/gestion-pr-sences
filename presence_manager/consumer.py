from djangochannelsrestframework.consumers import AsyncAPIConsumer


class PresenceConsumer(AsyncAPIConsumer):
    async def connect(self):
        await self.channel_layer.group_add("presence_group", self.channel_name)
        await super().connect()

    async def disconnect(self, code):
        await self.channel_layer.group_discard("presence_group", self.channel_name)
        await super().disconnect(code)

    async def send_presence_message(self, event):
        await self.send_json(event["message"])


from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.decorators import action
from django.http import JsonResponse


class PresenceConsumerSubmited(GenericAsyncAPIConsumer):
    """Consumer WebSocket pour gérer la soumission des présences via WebSocket.
    Il écoute les messages entrants et répond avec une confirmation JSON.
    Méthodes:
        - connect: Gère la connexion WebSocket.
        - disconnect: Gère la déconnexion WebSocket.
        - send_presence: Action pour traiter les données de présence soumises.


    """

    async def connect(self):
        self.group_name = "presence_group"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    @action()
    async def send_presence(self, request_id=None, **kwargs):
        data = kwargs
        print("Données reçues via WS SUBMIT :", data)

        # Réponse JSON directe à l'émetteur
        response = {
            "status": "success",
            "message": "Presence soumise avec succes via WebSocket.",
            "data": data,
            "timestamp": self.get_timestamp(),
        }

        # Retourner avec status code
        return response, 200

    def get_timestamp(self):
        from datetime import datetime

        return datetime.now().isoformat()


from channels.generic.websocket import AsyncJsonWebsocketConsumer


class GenerateSeance(AsyncJsonWebsocketConsumer):
    async def connect(self):
        # Le client rejoint le groupe "seances_du_jour"
        await self.channel_layer.group_add("seances_du_jour", self.channel_name)
        await self.accept()  # Accepte la connexion WebSocket

    async def disconnect(self, code):
        # Le client quitte le groupe
        await self.channel_layer.group_discard("seances_du_jour", self.channel_name)

    # Cette méthode correspond au type "nouvelle_seance"
    async def nouvelle_seance(self, event):
        await self.send_json(event["message"])


from channels.generic.websocket import AsyncWebsocketConsumer
import json


class SenderCours(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("presence_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("presence_group", self.channel_name)

    async def send_presence_message(self, event):
        await self.send(text_data=json.dumps(event["message"]))
