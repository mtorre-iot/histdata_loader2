#
# Mario Torre - 04/20/2023
#
class BackupFileError(Exception):
    def __init__(self, message):            
        super().__init__(message)

class ConfigFileWriteError(Exception):
    def __init__(self, message):            
        super().__init__(message)

class ConfigFileReadError(Exception):
    def __init__(self, message):            
        super().__init__(message)

class DataError(Exception):
    def __init__(self, message):            
        super().__init__(message)