from django.shortcuts import render

# Create your views here.


# -----------------------------------------creation utilisateur -------------------------------------------------
from rest_framework.generics import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import UtilisateurCreateSerializer


class UtilisateurCreateView(GenericAPIView):
    serializer_class = UtilisateurCreateSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "message": "Utilisateur créé avec succès.",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "nom": user.nom,
                    "postnom": user.postnom,
                    "role": user.role,
                }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
