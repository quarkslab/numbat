class NumbatException(Exception):
    pass

class SerializeException(NumbatException):
    pass

class DeserializeException(NumbatException):
    pass

class AlreadyOpenDatabase(NumbatException):
    pass

class NoDatabaseOpen(NumbatException):
    pass

