# presence_manager/consumers.py
# consumers.py
import urllib.parse
import uuid
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async

from django.core.exceptions import ObjectDoesNotExist


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
        from presence_manager.models import Classe

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
        from presence_manager.models import Etudiant, SeanceCours

        """
        content = JSON reçu depuis le client
        Exemple: {"username": "jordy", "age": 24}
        """

        # Traitement des données reçues si besoin
        #     matricule = payload.get("matricule")
        email = content.get("email")
        classe_nom = content.get("classe")
        cours_nom = content.get("cours")
        matricule = content.get("matricule")
        # ============================
        # 1. Vérification étudiant
        # ============================

        try:
            etudiant = await sync_to_async(
                Etudiant.objects.select_related("classe").get
            )(matricule=matricule)
        except ObjectDoesNotExist:
            return {"valid": False, "errors": {"matricule": "Étudiant introuvable."}}

        # Vérifier cohérence email
        if etudiant.utilisateur.email != email:
            return {
                "valid": False,
                "errors": {"email": "Email ne correspond pas à cet étudiant."},
            }

        print("JSON reçu :", content)

        # Réponse envoyée au client
        await self.send_json(
            {
                "status": "success",
                "message": "Donnees reçues avec succes.",
                "data_recue": {"username": email, "age": matricule},
            }
        )

    async def disconnect(self, close_code):
        print("Déconnexion WebSocket:", close_code)


#


class PresenceConsumer(AsyncJsonWebsocketConsumer):
    import json
    from channels.generic.websocket import AsyncJsonWebsocketConsumer
    from channels.db import database_sync_to_async

    from channels.generic.websocket import AsyncJsonWebsocketConsumer
    from channels.db import database_sync_to_async

    async def connect(self):
        self.seance_id = self.scope["url_route"]["kwargs"]["seance_id"]
        self.group_name = f"presence_seance_{self.seance_id}"

        # Join group
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # 1️⃣ Charger la liste existante
        await self.load_existing_presences()

        # Message de confirmation
        await self.send_json({"message": f"Connecte a la seance {self.seance_id}"})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def presence_update(self, event):
        """
        Reçoit les nouvelles présences en temps réel.
        """
        await self.send_json({"type": "new_presence", "presence": event["data"]})

    async def load_existing_presences(self):
        """
        Envoie toutes les présences déjà enregistrées pour cette séance.
        """
        presences = await self.get_presences_from_db()
        await self.send_json({"type": "existing_presences", "presences": presences})

    @database_sync_to_async
    def get_presences_from_db(self):
        from presence_manager.models import Presence

        try:
            queryset = Presence.objects.filter(seance_cours_id=self.seance_id).values(
                "id",
                "etudiant__matricule",
                "etudiant__utilisateur__nom",
                "etudiant__utilisateur__postnom",
                "present",
            )
            return list(queryset)

        except Exception as e:
            print("❌ ERREUR RÉCUP PRESENCES :", e)
            return []
