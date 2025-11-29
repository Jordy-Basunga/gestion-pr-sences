from cryptography.fernet import Fernet

# 1. Générer une clé unique et sécurisée (À stocker en sécurité !)
Encryptedkey = Fernet.generate_key()
cipher_suite = Fernet(Encryptedkey)


def encrypt_data(data: str) -> str:
    """Chiffre les données fournies."""
    encrypted_data = cipher_suite.encrypt(data.encode())
    return encrypted_data.decode()


def decrypt_data(encrypted_data: str) -> str:
    """Déchiffre les données fournies."""
    decrypted_data = cipher_suite.decrypt(encrypted_data.encode())
    return decrypted_data.decode()


#
# # 2. Chiffrer les données
# data = "Les données sensibles que je veux protéger".encode()
# encrypted_data = cipher_suite.encrypt(data)
# print("Données chiffrées :", encrypted_data)

# # 3. Déchiffrer les données (avec la même clé)
# decrypted_data = cipher_suite.decrypt(encrypted_data)
# print("Données déchiffrées :", decrypted_data.decode())
