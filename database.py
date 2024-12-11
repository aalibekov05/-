"Модуль для работы с базой данных"

import psycopg2
from psycopg2 import sql
from models import Pizza


class Pizza:
    def __init__(self, id, name, description, price):
        self.id = id
        self.name = name
        self.description = description
        self.price = price

    @classmethod
    def from_tuple(cls, data_tuple):
        return cls(*data_tuple)


class Database:
    def __init__(self):
        #Создаем подключение к базе данных
        self.conn = psycopg2.connect(
            dbname="pizza_db", user="postgres", password="root", host="localhost"
        )

        self.cursor = self.conn.cursor()

    def create_tables(self):
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role VARCHAR(50) NOT NULL
            );
            CREATE TABLE IF NOT EXISTS pizzas (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT NOT NULL,
                price DECIMAL(10, 2) NOT NULL
            );
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id),
                pizza_id INTEGER REFERENCES pizzas(id),
                status VARCHAR(50) NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self.conn.commit()

    def add_user(self, username, password_hash, role):
        self.cursor.execute("""
            INSERT INTO users (username, password_hash, role) 
            VALUES (%s, %s, %s)
        """, (username, password_hash, role))
        self.conn.commit()

    def get_user(self, username):
        self.cursor.execute("""
            SELECT * FROM users WHERE username = %s
        """, (username,))
        return self.cursor.fetchone()

    def add_pizza(self, name, description, price):
        try:
            price = float(price)  # Проверяем тип перед записью
            self.cursor.execute("""
                INSERT INTO pizzas (name, description, price) 
                VALUES (%s, %s, %s)
            """, (name, description, price))
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            print(f"Ошибка при добавлении пиццы: {e}")

    def get_pizzas(self):
        self.cursor.execute("SELECT * FROM pizzas")
        return [Pizza.from_tuple(row) for row in self.cursor.fetchall()]

    def add_order(self, user_id, pizza_id, status):
        self.cursor.execute("""
            INSERT INTO orders (user_id, pizza_id, status) 
            VALUES (%s, %s, %s)
        """, (user_id, pizza_id, status))
        self.conn.commit()

    def get_orders(self, user_id=None):
        if user_id:
            self.cursor.execute("""
                SELECT o.id, p.name, o.status, o.date
                FROM orders o
                JOIN pizzas p ON o.pizza_id = p.id
                WHERE o.user_id = %s
                ORDER BY o.date DESC
            """, (user_id,))
        else:
            self.cursor.execute("""
                SELECT o.id, u.username, p.name, o.status, o.date
                FROM orders o
                JOIN users u ON o.user_id = u.id
                JOIN pizzas p ON o.pizza_id = p.id
                ORDER BY o.date DESC
            """)
        return self.cursor.fetchall()

    def get_pizzas(self):
        self.cursor.execute("SELECT id, name, description, price FROM pizzas")
        return [Pizza.from_tuple(row) for row in self.cursor.fetchall()]

    def update_order_status(self, order_id, status):
        self.cursor.execute("""
            UPDATE orders SET status = %s WHERE id = %s
        """, (status, order_id))
        self.conn.commit()

    def delete_pizza(self, pizza_id):
        # Устанавливаем статус "Отменён" для всех заказов, связанных с пиццей
        self.cursor.execute("""
            UPDATE orders SET status = 'Отменён' WHERE pizza_id = %s
        """, (pizza_id,))
        self.conn.commit()

        # Удаляем пиццу
        self.cursor.execute("DELETE FROM pizzas WHERE id = %s", (pizza_id,))
        self.conn.commit()
        print(f"Пицца ID {pizza_id} удалена, заказы обновлены.")

    def update_pizza(self, pizza_id, name, description, price):
        self.cursor.execute("""
            UPDATE pizzas SET name = %s, description = %s, price = %s WHERE id = %s
        """, (name, description, price, pizza_id))
        self.conn.commit()

    def get_pizza_by_id(self, pizza_id):
        self.cursor.execute("SELECT * FROM pizzas WHERE id = %s", (pizza_id,))
        row = self.cursor.fetchone()
        return Pizza.from_tuple(row)

    """Закрыть соединение """
    def close(self):
        self.cursor.close()
        self.conn.close()
