from mint import mint_error

class ItemNotFound(mint_error.MintError):
    pass

class ProductNotFound(ItemNotFound):
    pass

class ProductVersionNotFound(ItemNotFound):
    pass

class UserNotFound(ItemNotFound):
    pass

class MemberNotFound(ItemNotFound):
    pass

PermissionDenied = mint_error.PermissionDenied
