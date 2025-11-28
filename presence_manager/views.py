from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .serializer import PresenceSubmitSerializer
from .models import Etudiant, Classe, Cours, Presence, SeanceCours
from django.utils.timezone import now


@api_view(["POST"])
def submit_presence(request):
    # 🔎 Valider les données via serializer
    serializer = PresenceSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    print(data)
    matricule = data["matricule"]
    email = data["email"]
    classe_code = data["classe"]
    cours_code = data["cours"]

    # --- Vérifications BD ---
    try:
        etudiant = Etudiant.objects.get(matricule=matricule)
    except Etudiant.DoesNotExist:
        return Response(
            {"error": "Étudiant introuvable."}, status=status.HTTP_404_NOT_FOUND
        )

    try:
        classe = Classe.objects.get(id=classe_code)
    except Classe.DoesNotExist:
        return Response(
            {"error": "Classe introuvable."}, status=status.HTTP_404_NOT_FOUND
        )

    # 🔍 Vérifier que l'étudiant appartient bien à cette classe
    if not classe.etudiants.filter(id=etudiant.id).exists():
        return Response(
            {"error": "Cet étudiant n'appartient pas à cette classe."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        cours = Cours.objects.get(id=cours_code, classe=classe)
    except Cours.DoesNotExist:
        return Response(
            {"error": "Cours introuvable dans cette classe."},
            status=status.HTTP_404_NOT_FOUND,
        )

        # ✔ Vérifier s'il existe une séance EN COURS aujourd'hui
    today = now().date()

    seance = SeanceCours.objects.filter(
        horaire_cours__cours=cours, date_seance=today, status="en_cours"
    ).first()
    print(seance)
    if not seance:
        return Response({"error": "Aucune séance en cours pour ce cours."}, status=400)

    # --- Enregistrement ---

    presence = Presence.objects.filter(
        seance_cours=seance,
        etudiant=etudiant,
        present=True,
    ).exists()

    if presence:
        return Response({"error": "Vous etes deja dans la liste"}, status=400)

    presence = Presence.objects.create(
        seance_cours=seance,
        etudiant=etudiant,
        present=True,
    )

    presence.save()

    # # --- WebSocket en temps réel ---
    # channel_layer = get_channel_layer()
    # async_to_sync(channel_layer.group_send)(
    #     f"presence_{classe.id}",
    #     {
    #         "type": "presence_update",  # doit exister dans ton consumer
    #         "data": {
    #             "matricule": etudiant.matricule,
    #             "etudiant": etudiant.utilisateur.nom,
    #             "cours": cours.nom,
    #             "classe": classe.code,
    #             "status": "present",
    #         },
    #     },
    # )

    # # --- Réponse HTTP ---
    # return Response(
    #     {
    #         "message": "Présence enregistrée avec succès.",
    #         "presence": {
    #             "etudiant": etudiant.utilisateur.nom,
    #             "matricule": etudiant.matricule,
    #             "classe": classe.code,
    #             "cours": cours.nom,
    #         },
    #     },
    #     status=status.HTTP_201_CREATED,
    # )
    return Response({"message": "ok"})
