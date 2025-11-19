# presence_manager/consumers.py
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class SeancesConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer WebSocket pour envoyer les séances du jour aux Terminaux des classes.
    """

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("seances_du_jour", self.channel_name)

    async def disconnect(self, code):
        await self.channel_layer.group_discard("seances_du_jour", self.channel_name)

    async def send_seances(self, event):
        """
        Méthode appelée depuis le scheduler / task pour envoyer les séances
        """
        await self.send_json(event["message"])
