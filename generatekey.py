from cryptography.fernet import Fernet
key = Fernet.generate_key()
print(key.decode())  # Output: e.g., 'bXh5c2E0aW1uZ2tvcXJ0eXppdmJwbnd4YzEyMzQ1Njc4OTA='