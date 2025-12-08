import json
import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv


# Charger la clé de chiffrement depuis une variable d'environnement
load_dotenv()

FERNET_KEY = os.getenv("FERNET_KEY")
cipher_suite = Fernet(FERNET_KEY)



def encrypt_data(data) -> str:
    """Chiffre les données fournies."""
    # Si c’est un dict → convertir en JSON
    if isinstance(data, dict):
        data = json.dumps(data)
    
    # Si ce n’est pas une string → erreur
    if not isinstance(data, str):
        raise ValueError("Les données doivent être une string JSON ou un dict.")

    encrypted_data = cipher_suite.encrypt(data.encode())
    return encrypted_data.decode()


def decrypt_data(encrypted_data) -> str:
    """Déchiffre les données fournies."""
    decrypted_data = cipher_suite.decrypt(encrypted_data.encode())
    data = decrypted_data.decode()
    return data


#
# # 2. Chiffrer les données
# data = "Les données sensibles que je veux protéger".encode()
# encrypted_data = cipher_suite.encrypt(data)
# print("Données chiffrées :", encrypted_data)

# # 3. Déchiffrer les données (avec la même clé)
# decrypted_data = cipher_suite.decrypt(encrypted_data)
# print("Données déchiffrées :", decrypted_data.decode())
