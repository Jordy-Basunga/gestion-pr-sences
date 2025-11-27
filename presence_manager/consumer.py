# presence_manager/consumers.py
# consumers.py
import urllib.parse
import uuid
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async


class SeancesConsumer(AsyncJsonWebsocketConsumer):
    """
    Consumer WebSocket pour envoyer les séances du jour aux Terminaux des classes.
    """

    async def connect(self):
        query = urllib.parse.parse_qs(self.scope["query_string"].decode())
        terminal_id = query.get("terminal_id", [None])[0]
        print(f"[WS] Nouvelle connexion terminal_id={terminal_id}")
        if not terminal_id:
            await self.close()
            return

        # ------------------------------------
        self.classe = await sync_to_async(self._get_classe)(terminal_id)
        print(f"[WS] Classe trouvée pour terminal_id={terminal_id}: {self.classe}")
        if not self.classe:
            await self.close()
            return

        # Créer le nom du groupe
        self.group_name = f"classe_{self.classe.id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        print(f"NOUVEAU GROUPE : {self.group_name}")
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_seances(self, event):
        """
        Méthode appelée depuis le scheduler / task pour envoyer les séances
        """
        print(
            f"!!! MESSAGE REÇU dans le consumer pour le groupe {self.group_name} !!!"
        )  # <- Ajoutez ceci
        await self.send_json(event["message"])

    def _get_classe(self, terminal_uuid):
        """
        la fonction perme
        """
        from .models import Classe  # import ici aussi

        try:
            return Classe.objects.get(code_terminal=terminal_uuid)
        except Classe.DoesNotExist:
            return None


import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class SubmitePresence(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send_json({"message": "WebSocket connecté avec succès."})

    async def receive_json(self, content, **kwargs):
        """
        content = JSON reçu depuis le client
        Exemple: {"username": "jordy", "age": 24}
        """

        # Traitement des données reçues si besoin
        username = content.get("username")
        age = content.get("age")

        print("JSON reçu :", content)

        # Réponse envoyée au client
        await self.send_json(
            {
                "status": "success",
                "message": "Données reçues avec succès.",
                "data_recue": {"username": username, "age": age},
            }
        )

    async def disconnect(self, close_code):
        print("Déconnexion WebSocket:", close_code)
