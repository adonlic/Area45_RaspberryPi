class ObjectHolder:
    # keeps object when assigning it from in-function variable to non-function variable
    def __init__(self):
        self.__object = None

    def hold(self, object_to_hold):
        self.__object = object_to_hold

    def access(self):
        return self.__object
