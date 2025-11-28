from rest_framework import serializers


class PresenceSubmitSerializer(serializers.Serializer):
    matricule = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    classe = serializers.CharField(required=True)
    cours = serializers.CharField(required=True)
