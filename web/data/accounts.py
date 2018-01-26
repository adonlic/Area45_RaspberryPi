from datetime import datetime
from string import ascii_letters, digits
import random

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker


Base = declarative_base()


class Account(Base):
    __tablename__ = 'account'
    __table_args__ = {'info': {'without_rowid': True}}

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)
    api_key = Column(String, nullable=True)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)

    def __init__(self, username, password, role, created_at, updated_at):
        self.username = username
        self.password = password
        self.role = role
        self.created_at = created_at
        self.updated_at = updated_at


class DBHandler:
    __instance = None

    @staticmethod
    def init(base, db_url):
        DBHandler.__instance = DBHandler(base, db_url)

    @staticmethod
    def get_instance():
        return DBHandler.__instance

    def __init__(self, base, db_url):
        self.__engine = create_engine('sqlite:///' + db_url)
        self.__session = scoped_session(sessionmaker(bind=self.__engine))

        base.metadata.create_all(self.__engine)

    def get_accounts(self):
        accounts = self.__session.query(Account).all()

        return accounts

    def new_account(self, username, password, role, key_size):
        account = self.__session.query(Account).filter(Account.username == username).first()

        if account is None:
            created_at = DBHandler.__get_str_formatted_datetime()
            account = Account(username, password, role, created_at, created_at)
            message = ""

            # automatically assign API key to collector...
            if role == 'collector':
                account.api_key = DBHandler.__generate_api_key(key_size)
                message = "\nAPI key is assigned to '{}'".format(username)

            self.__session.add(account)
            self.__session.commit()

            return True, "User '{}' with role '{}' is successfully added to database{}".format(username, role, message)

        return False, "Account with username '{}' already exists".format(username)

    def assign_api_key(self, username, size):
        account = self.__session.query(Account).filter(Account.username == username).first()

        if account is not None:
            if account.role == 'collector':
                account.api_key = DBHandler.__generate_api_key(size)
                account.updated_at = DBHandler.__get_str_formatted_datetime()
                self.__session.commit()

                return True, "API key is assigned to '{}'".format(username)
            elif account.role == 'admin':
                return False, "Admin has all rights and cannot be assigned with API key"
            # else if it's 'other' role...
            return False, "Cannot assign API key to users with role 'other'"

        return False, "Account with username '{}' doesn't exist".format(username)

    def change_account_role(self, username, role, key_size):
        account = self.__session.query(Account).filter(Account.username == username).first()

        if account is not None:
            if role == account.role:
                return False, "User '{}' is already has role '{}'".format(username, role)
            else:
                account.role = role
                account.updated_at = DBHandler.__get_str_formatted_datetime()
                message = ""

                if role == 'collector':
                    account.api_key = DBHandler.__generate_api_key(key_size)
                    message = "\nAPI key is assigned to '{}'".format(username)
                else:
                    account.api_key = None

                return True, "User '{}' now has role '{}'{}".format(username, role, message)

        return False, "Account with username '{}' doesn't exist".format(username)

    def delete_account(self, username):
        account = self.__session.query(Account).filter(Account.username == username).first()

        if account is not None:
            self.__session.delete(account)
            self.__session.commit()

            return True, "User '{}' is successfully deleted".format(username)

        return False, "Account with username '{}' doesn't exist".format(username)

    def is_valid_api_key(self, api_key):
        # only collector can have api key
        accounts = self.__session.query(Account).filter(Account.role == 'collector').all()

        for account in accounts:
            if account.api_key == api_key:
                return True, "'{}'\'s API key found".format(account.username)

        return False, "Given API key doesn't exist"

    @staticmethod
    def __get_str_formatted_datetime():
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @staticmethod
    def __generate_api_key(size):
        chars = ascii_letters + digits

        return ''.join(random.choice(chars) for _ in range(size))
