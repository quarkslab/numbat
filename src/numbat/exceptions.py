class NumbatException(Exception):
    pass

class SerializeException(NumbatException):
    pass

class DeserializeException(NumbatException):
    pass

class AlreayOpenDatabase(NumbatException):
    pass

class NoDatabaseOpen(NumbatException):
    pass

