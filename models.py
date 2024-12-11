'''Модуль для описания моделей в базе данных'''
from hashlib import sha256

#Описывает модель пользователя
class User:
    def __init__(self, id, username, password_hash, role):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role

    @staticmethod
    def hash_password(password):
        return sha256(password.encode()).hexdigest()

#Описывает модель пиццы
class Pizza:
    def __init__(self, id, name, description, price):
        self.id = id
        self.name = name
        self.description = description
        self.price = price


