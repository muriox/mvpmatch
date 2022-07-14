from rest_framework import status

# Models constants
ROLES = [('SR', 'SELLER'), ('BR', 'BUYER'), ('ADMIN', 'ADMIN')]
ALLOWED_COINS = [5, 10, 20, 50, 100]
ALLOWED_COINS_MESSAGE = "Coin not allowed. Only 5, 10, 20, 50 and 100 are allow."

# Token constants
TOKEN_EXPIRE_TIME = 60  # 1HOUR (60 minutes)
TOKEN_NOT_FOUND_INVALID_MSG = {"status": status.HTTP_400_BAD_REQUEST,
                               "message": "Token Not Found/Expired/Invalid/logout/MissingUsername. Please re-login"}
BUYER_ENDPOINTS = ["/api/v{*}/user", "/api/v{*}/deposit", "/api/v{*}/buy", "/api/v{*}/logout",
                   "/api/v{*}/logout/all"]
SELLER_ENDPOINTS = ["/api/v{*}/user", "/api/v{*}/product", "/api/v{*}/logout",
                    "/api/v{*}/logout/all"]

