import os

from shared.utils.validator import is_not_empty, is_one_of_values
from web.loader import load, logger, account_db_handler


__API_KEY_SIZE = 50


def start():
    config_path = os.getcwd().split('\\')
    config_path = config_path[:config_path.index('web') + 1]
    config_location = '\\'.join(config_path)
    ok, info = load(config_location)

    if not ok:
        return

    while True:
        print("Work with accounts:")
        print("\t1) list all accounts")
        print("\t2) new account")
        print("\t3) assign/update api key")
        print("\t4) change account role")
        print("\t5) delete account")
        print("\t6) exit")
        answer = input(":> ")

        try:
            choice = int(answer)

            if choice == 1:
                accounts = account_db_handler.access().get_accounts()

                if len(accounts) == 0:
                    print("There are no accounts")
                else:
                    print("Accounts:")
                    for account in accounts:
                        print("\t{} [{}]".format(account.username, account.role))
                        if account.api_key is not None:
                            print("\t\tAPI key:\t{}".format(account.api_key))
                        print("\t\tcreated at:\t{}".format(account.created_at))
                        print("\t\tupdated at:\t{}".format(account.updated_at))
            elif choice == 2:
                username = input("username: ")
                ok, message = is_not_empty(username)

                if ok:
                    password = input("password: ")
                    ok, message = is_not_empty(password)

                    if ok:
                        if len(password) < 6:
                            ok = False
                            message = "Password must have minimum 6 characters"

                        # password must be at least 6 characters in length
                        if ok:
                            role = input("role (admin, collector, other): ")
                            ok, message = is_one_of_values(role, ['admin', 'collector', 'other'])

                            if ok:
                                ok, message = account_db_handler.access()\
                                    .new_account(username, password, role, __API_KEY_SIZE)
                                # print to logger only if successful...
                                logger.access().info(message)

                print(message)
            elif choice == 3:
                username = input("username: ")
                ok, message = is_not_empty(username)

                if ok:
                    ok, message = account_db_handler.access().assign_api_key(username, __API_KEY_SIZE)
                    logger.access().info(message)

                print(message)
            elif choice == 4:
                username = input("username: ")
                ok, message = is_not_empty(username)

                if ok:
                    role = input("role (admin, collector, other): ")
                    ok, message = is_one_of_values(role, ['admin', 'collector', 'other'])

                    if ok:
                        ok, message = account_db_handler.access().change_account_role(username, role, __API_KEY_SIZE)
                        logger.access().info(message)

                print(message)
            elif choice == 5:
                username = input("username: ")
                ok, message = is_not_empty(username)

                if ok:
                    ok, message = account_db_handler.access().delete_account(username)
                    logger.access().info(message)

                print(message)
            elif choice == 6:
                print("Application is shutting down...")
                break
            else:
                print("Given option doesn't exist")
        except ValueError:
            print("Invalid input format")


if __name__ == '__main__':
    start()
