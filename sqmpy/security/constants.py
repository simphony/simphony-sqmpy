from enum import Enum, unique


@unique
class UserRole(Enum):
    """
    Defines user roles
    """
    admin = 0
    staff = 1
    user = 2


@unique
class UserStatus(Enum):
    """
    Defines user status
    """
    new = 0
    active = 1
    inactive = 2
