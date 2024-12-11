from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLineEdit, QLabel, QFormLayout, \
    QTableWidget, QTableWidgetItem, QComboBox, QMainWindow, QMessageBox
from PyQt6.QtCore import Qt, QFile, QTextStream
from PyQt6.lupdate import user

from models import User, Pizza
from database import Database
import hashlib

"Создание окна"
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.create_tables()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Регситрация')  # Устанавливаем заголовок окна
        self.setWindowIcon(QIcon('./auth.png'))  # Устанавливаем иконку окна

        self.resize(600, 400)
        self.layout = QVBoxLayout()

        # Форма входа
        self.login_form = QWidget()
        self.login_layout = QFormLayout()
        self.username_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_button = QPushButton('Войти')
        self.register_button = QPushButton('Зарегистрироваться')

        self.login_layout.addRow('Логин:', self.username_input)
        self.login_layout.addRow('Пароль:', self.password_input)
        self.login_layout.addWidget(self.login_button)
        self.login_layout.addWidget(self.register_button)
        self.login_form.setLayout(self.login_layout)

        self.layout.addWidget(self.login_form)
        self.setLayout(self.layout)

        # Привязка кнопок
        self.login_button.clicked.connect(self.login)
        self.register_button.clicked.connect(self.register)

        self.apply_stylesheet()

    def apply_stylesheet(self):
        """Простой стиль без тяжелого фона"""
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #f5f5f5, stop: 1 #e0e0e0
                );
                font-family: Arial, sans-serif;
                color: #333;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                text-align: center;
                font-size: 14px;
                margin: 4px 2px;
                cursor: pointer;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QLineEdit {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
        """)
    #Авторизация
    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        user_data = self.db.get_user(username)

        if user_data:
            user = User(*user_data)
            if user.password_hash == hashlib.sha256(password.encode()).hexdigest():
                self.username_input.clear()
                self.password_input.clear()
                self.show_menu(user)
            else:
                self.show_error('Неверные данные для входа')
        else:
            self.show_error('Пользователь не найден')
    #Регистрация
    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()

        if username and password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            self.db.add_user(username, password_hash, 'Покупатель')
            self.show_info('Успешная регистрация')
        else:
            self.show_error('Заполните все поля')

    """Выводит окно с заказами пользователя"""

    def show_user_orders(self, user):
        self.orders_window = QWidget()
        self.orders_window.setWindowTitle("Мои заказы")
        self.orders_layout = QVBoxLayout()


        orders = self.db.get_orders(user.id)
        if orders:
            self.orders_table = QTableWidget()
            self.orders_table.setRowCount(len(orders))
            self.orders_table.setColumnCount(3)
            self.orders_table.setHorizontalHeaderLabels(['Пицца', 'Статус', 'Действие'])

            for row, order in enumerate(orders):
                self.orders_table.setItem(row, 0, QTableWidgetItem(order[1]))  # Название пиццы
                self.orders_table.setItem(row, 1, QTableWidgetItem(order[2]))  # Статус

                if order[2] != 'Отменён':
                    cancel_button = QPushButton('Отменить')
                    cancel_button.clicked.connect(lambda _, order_id=order[0]: self.cancel_order(order_id))
                    self.orders_table.setCellWidget(row, 2, cancel_button)
            self.orders_layout.addWidget(self.orders_table)
        else:
            no_orders_label = QLabel("У вас пока нет заказов.")
            self.orders_layout.addWidget(no_orders_label)

        self.orders_window.setLayout(self.orders_layout)
        self.orders_window.show()

    #Отмена заказа
    def cancel_order(self, order_id):
        self.db.update_order_status(order_id, 'Отменён')
        self.show_info('Заказ успешно отменён')
        if hasattr(self, 'orders_window') and self.orders_window.isVisible():
            self.orders_window.close()
            self.show_user_orders(self.current_user)

    #Показывает меню пользователю
    def show_menu(self, user):
        self.menu_window = QWidget()
        self.menu_layout = QVBoxLayout()
        self.menu_window.setWindowTitle('Меню')


        self.pizza_list = QTableWidget()
        pizzas = self.db.get_pizzas()
        self.pizza_list.setRowCount(len(pizzas))
        self.pizza_list.setColumnCount(3 if user.role == 'admin' else 4)
        headers = ['Название', 'Описание', 'Цена'] + (['Заказ'] if user.role == 'Покупатель' else [])
        self.pizza_list.setHorizontalHeaderLabels(headers)

        for row, pizza in enumerate(pizzas):
            self.pizza_list.setItem(row, 0, QTableWidgetItem(pizza.name))
            self.pizza_list.setItem(row, 1, QTableWidgetItem(pizza.description))
            self.pizza_list.setItem(row, 2, QTableWidgetItem(str(pizza.price)))

            if user.role == 'Покупатель':
                order_button = QPushButton('Заказать')
                order_button.clicked.connect(lambda _, pizza_id=pizza.id: self.place_order(user, pizza_id))
                self.pizza_list.setCellWidget(row, 3, order_button)

        self.menu_layout.addWidget(self.pizza_list)

        if user.role == 'Покупатель':
            self.view_orders_button = QPushButton('Просмотреть заказы')
            self.view_orders_button.clicked.connect(lambda: self.show_user_orders(user))
            self.menu_layout.addWidget(self.view_orders_button)
        elif user.role == 'admin':
            self.add_pizza_button = QPushButton('Добавить пиццу')
            self.add_pizza_button.clicked.connect(self.add_pizza)
            self.manage_pizzas_button = QPushButton('Управлять пиццами')
            self.orders_window = QWidget()
            self.orders_window.setWindowTitle("Мои заказы")
            self.add_pizza_window = QWidget()
            self.add_pizza_layout = QVBoxLayout()
            self.add_pizza_window.setWindowTitle("Добавление новой пиццы")
            self.manage_pizza_window = QWidget()
            self.manage_pizza_window.setWindowTitle("Управление пиццами")
            self.manage_pizzas_button.clicked.connect(self.manage_pizzas)
            self.menu_layout.addWidget(self.add_pizza_button)
            self.menu_layout.addWidget(self.manage_pizzas_button)

        self.menu_window.setLayout(self.menu_layout)

        self.menu_window.show()


    #Оформить заказ
    def place_order(self, user, pizza_id):
        self.db.add_order(user.id, pizza_id, 'Ожидание')
        self.show_info('Заказ успешно размещен')

    #Меню админа
    def admin_controls(self, user):
        self.add_pizza_button = QPushButton('Добавить позицию')
        self.add_pizza_button.clicked.connect(self.add_pizza)

        self.orders_button = QPushButton('Управлять заказами')
        self.orders_button.clicked.connect(self.manage_orders)

        self.menu_layout.addWidget(self.add_pizza_button)
        self.menu_layout.addWidget(self.orders_button)

    #Окошко для добавления пиццы
    def add_pizza(self):
        self.add_pizza_window = QWidget()
        self.add_pizza_window.setWindowTitle("Добавление новой пиццы")
        self.add_pizza_layout = QFormLayout()
        self.pizza_name_input = QLineEdit()
        self.pizza_description_input = QLineEdit()
        self.pizza_price_input = QLineEdit()
        self.add_pizza_submit_button = QPushButton('Добавить пиццу')

        self.add_pizza_layout.addRow('Название:', self.pizza_name_input)
        self.add_pizza_layout.addRow('Описание:', self.pizza_description_input)
        self.add_pizza_layout.addRow('Цена:', self.pizza_price_input)
        self.add_pizza_layout.addWidget(self.add_pizza_submit_button)

        self.add_pizza_window.setLayout(self.add_pizza_layout)
        self.add_pizza_submit_button.clicked.connect(self.save_pizza)

        self.add_pizza_window.show()

    #Добавить пиццу в базу данных
    def save_pizza(self):
        try:
            name = self.pizza_name_input.text().strip()
            description = self.pizza_description_input.text().strip()
            price_text = self.pizza_price_input.text().strip()


            # Проверка ввода
            if not price_text.replace('.', '', 1).isdigit():
                raise ValueError("Цена должна быть числом.")
            price = float(price_text)

            if not name or not description or price <= 0:
                raise ValueError("Заполните все поля корректно.")

            # Добавляем пиццу в базу данных
            self.db.add_pizza(name, description, price)

            self.show_info('Пицца добавлена успешно!')

            # Закрываем окно добавления и обновляем таблицу
            self.add_pizza_window.close()
            self.refresh_pizza_list()

        except ValueError as e:
            self.show_error(str(e))
        except Exception as e:
            self.show_error(f"Ошибка: {e}")

    def refresh_pizza_list(self):
        if hasattr(self, 'pizza_list') and self.pizza_list:
            pizzas = self.db.get_pizzas()
            self.pizza_list.setRowCount(len(pizzas))

            for row, pizza in enumerate(pizzas):
                self.pizza_list.setItem(row, 0, QTableWidgetItem(pizza.name))
                self.pizza_list.setItem(row, 1, QTableWidgetItem(pizza.description))
                self.pizza_list.setItem(row, 2, QTableWidgetItem(str(pizza.price)))

                # Если пользователь — покупатель, добавляем кнопку "Заказать"
                if hasattr(self, 'current_user') and self.current_user.role == 'Покупатель':
                    order_button = QPushButton('Заказать')
                    order_button.clicked.connect(
                        lambda _, pizza_id=pizza.id: self.place_order(self.current_user, pizza_id))
                    self.pizza_list.setCellWidget(row, 3, order_button)

    #Изменить статус заказа
    def update_order_status(self, order_id, status):
        self.db.update_order_status(order_id, status)
        self.show_info('Заказ обновлен успешно')

    #Выводит все пиццы, можно удалить или изменить пиццу
    def manage_pizzas(self):
        self.manage_pizza_window = QWidget()
        self.manage_pizza_window.setWindowTitle("Управление пиццами")
        self.manage_pizza_layout = QVBoxLayout()

        self.pizza_table = QTableWidget()
        pizzas = self.db.get_pizzas()
        self.pizza_table.setRowCount(len(pizzas))
        self.pizza_table.setColumnCount(5)
        self.pizza_table.setHorizontalHeaderLabels(['ID', 'Название', 'Описание', 'Цена', 'Действие'])

        for row, pizza in enumerate(pizzas):
            self.pizza_table.setItem(row, 0, QTableWidgetItem(str(pizza.id)))
            self.pizza_table.setItem(row, 1, QTableWidgetItem(pizza.name))
            self.pizza_table.setItem(row, 2, QTableWidgetItem(pizza.description))
            self.pizza_table.setItem(row, 3, QTableWidgetItem(str(pizza.price)))

            # Кнопка удаления
            delete_button = QPushButton('Удалить')
            delete_button.clicked.connect(lambda checked, pizza_id=pizza.id: self.delete_pizza(pizza_id))
            self.pizza_table.setCellWidget(row, 4, delete_button)

        self.manage_pizza_layout.addWidget(self.pizza_table)
        self.manage_pizza_window.setLayout(self.manage_pizza_layout)
        self.manage_pizza_window.show()

    #Удаление пиццы
    def delete_pizza(self, pizza_id):
        confirmation = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Все заказы, связанные с пиццей ID {pizza_id}, будут отменены. Продолжить?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirmation == QMessageBox.StandardButton.Yes:
            self.db.delete_pizza(pizza_id)
            self.show_info("Пицца успешно удалена! Связанные заказы были обновлены.")
            self.refresh_manage_pizzas()

    def refresh_manage_pizzas(self):
        """Обновляет окно управления пиццами"""
        if hasattr(self, 'manage_pizza_window') and self.manage_pizza_window.isVisible():
            self.manage_pizza_window.close()
        self.manage_pizzas()
    #Изменить пиццу
    def edit_pizza(self, pizza_id):
        pizza = self.db.get_pizza_by_id(pizza_id)

        self.edit_pizza_window = QWidget()
        self.edit_pizza_layout = QFormLayout()

        self.pizza_name_input = QLineEdit(pizza.name)
        self.pizza_description_input = QLineEdit(pizza.description)
        self.pizza_price_input = QLineEdit(str(pizza.price))
        self.save_pizza_button = QPushButton('Сохранить изменения')

        self.edit_pizza_layout.addRow('Название:', self.pizza_name_input)
        self.edit_pizza_layout.addRow('Описание:', self.pizza_description_input)
        self.edit_pizza_layout.addRow('Цена:', self.pizza_price_input)
        self.edit_pizza_layout.addWidget(self.save_pizza_button)

        self.save_pizza_button.clicked.connect(lambda: self.save_pizza_changes(pizza_id))

        self.edit_pizza_window.setLayout(self.edit_pizza_layout)
        self.edit_pizza_window.show()

    #Сохранить изменения пиццы
    def save_pizza_changes(self, pizza_id):
        name = self.pizza_name_input.text()
        description = self.pizza_description_input.text()
        price = float(self.pizza_price_input.text())

        if name and description and price:
            self.db.update_pizza(pizza_id, name, description, price)
            self.show_info('Пицца успешно обновлена')
            self.edit_pizza_window.close()
            self.manage_pizzas()
        else:
            self.show_error('Заполните все поля')

    #Управление заказами
    def manage_orders(self):
        self.orders_window = QWidget()
        self.orders_layout = QVBoxLayout()

        self.orders_table = QTableWidget()
        orders = self.db.get_orders()
        self.orders_table.setRowCount(len(orders))
        self.orders_table.setColumnCount(5)
        self.orders_table.setHorizontalHeaderLabels(['User', 'Pizza', 'Status', 'Date', 'Actions'])

        for row, order in enumerate(orders):
            self.orders_table.setItem(row, 0, QTableWidgetItem(str(order[1])))
            self.orders_table.setItem(row, 1, QTableWidgetItem(str(order[2])))
            self.orders_table.setItem(row, 2, QTableWidgetItem(order[3]))
            self.orders_table.setItem(row, 3, QTableWidgetItem(str(order[4])))

            # Добавляем кнопки для изменения статуса
            status_button = QComboBox()
            status_button.addItems(['Ожидание', 'Доставлена', 'Отменена'])
            status_button.setCurrentText(order[3])
            status_button.currentTextChanged.connect(
                lambda status, order_id=order[0]: self.update_order_status(order_id, status))
            self.orders_table.setCellWidget(row, 4, status_button)

        self.orders_layout.addWidget(self.orders_table)
        self.orders_window.setLayout(self.orders_layout)
        self.orders_window.show()

    #Выводит текст в консоль
    def show_info(self, message):
        QMessageBox.information(self, "Информация", message)

    #Выводит ошибку в консоль
    def show_error(self, message):
        QMessageBox.critical(self, "Ошибка", message)

#Окно с пиццами
class PizzaMenuWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Меню пицц")


        # Применяем стили для этого окна
        self.apply_stylesheet()

        # Инициализация элементов интерфейса
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Меню пицц")

        layout = QVBoxLayout()

        self.label = QLabel("Choose your pizza!")
        layout.addWidget(self.label)

        self.pizza_button = QPushButton("Order Pizza")
        layout.addWidget(self.pizza_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def apply_stylesheet(self):
        """Загружаем и применяем файл стилей ко всем виджетам"""
        file = QFile("style.css")
        file.open(QFile.OpenModeFlag.ReadOnly)
        stylesheet = QTextStream(file).readAll()
        self.setStyleSheet(stylesheet)






#Запуск программы
if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.setWindowTitle("Авторизация")
    window.show()
    app.exec()
