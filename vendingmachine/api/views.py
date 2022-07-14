from django.contrib.auth.hashers import make_password
from .constants import ALLOWED_COINS, BUYER_ENDPOINTS, SELLER_ENDPOINTS, ALLOWED_COINS_MESSAGE
from .util import *
import json
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponse
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.utils import IntegrityError


def home(request):
    return HttpResponse(json.dumps({'api': 'Vending Machine API', 'developer': 'Mudashiru'}),
                        content_type="application/json")


def api_versions(request):
    return HttpResponse(json.dumps({'version': 'v1', 'stable': 'v1', 'beta': 'None'}),
                        content_type="application/json")


def api_v1(request):
    return HttpResponse(json.dumps(
        {'version': 'v1', 'description': 'First implementation of MVP Match Vending Machine API'}),
        content_type="application/json")


def test(request):
    pass


class UserView(APIView):
    """
    User view for requests
    """

    def post(self, request):
        """
        Create a user
        :param request:
        :return: response status and message
        """
        data = {}

        # Check deposit coin
        if not int(request.data.get('deposit')) in ALLOWED_COINS:
            return Response({"status": "User creation failed"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Prepare data
        data['username'] = str(request.data.get('username')).lower()
        # Encrypt password
        new_pass = make_password(request.data.get('password'))
        data["password"] = new_pass
        data['role'] = str(request.data.get('role')).upper()
        data['deposit'] = request.data.get('deposit')

        # Serialize, validate and save
        serializer = UserSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response({"status": "User creation successful",
                             "data": serializer.data},
                            status=status.HTTP_200_OK)
        else:
            return Response({"status": "User creation failed",
                             "data": serializer.data},
                            status=status.HTTP_406_NOT_ACCEPTABLE)


class LoginView(APIView):
    """
    Login view for POST request
    """

    def post(self, request):
        """
        Validate login request a user
        :param request:
        :return: response status and message
        """
        # Check login details
        username = request.data.get('username').lower()
        password = request.data.get('password')

        # Validate login details
        if not username or not password:
            return Response({"status": status.HTTP_404_NOT_FOUND, "message": "Invalid Username/Password input"})

        # Declare util
        token_util = TokenUtil()
        # Validate login details
        login_check = token_util.check_username_and_password(username, password)

        if login_check:
            # Check if any token exist for this user, if not create one
            token_exist = token_util.token_exist(username)
            if not token_exist:
                # Generate New Token
                token_util.create_token(username)
            print("1")
            # Check is token has expired
            token = token_util.get_token_by_username(username)
            token_expired = token_util.is_token_expired(token.key)
            if token_expired:
                # Delete old token
                token_util.delete_token(token.key)
                # Generate New Token
                new_token = token_util.create_token(username)

                return Response({"message": "Your token has expired, new token generated.", "new-token": new_token})
            print("2")

            # Check if user is currently login
            if token.login:
                return Response({"status": status.HTTP_205_RESET_CONTENT,
                                 "message": "User is logged in.",
                                 "hint": "request DELETE at api/v{*}/logout/all endpoint to terminate sessions."})
            else:
                # Update login status.
                token_util.update_login(token.id, True)
                # Provide endpoint hint for different User type
                if token.user.role == 'BR':
                    endpoints = BUYER_ENDPOINTS
                else:
                    endpoints = SELLER_ENDPOINTS

                return Response({"message": "Login successful",
                                 "token": token.key, "paths": endpoints})
        else:
            return Response({"message": "Invalid Username/Password"})


class LogoutView(APIView):
    """
    Logout view for POST request
    """

    def get(self, request):
        """
        Validate login request a user
        :param request:
        :return: response status and message
        """
        # Get token key
        key = request.data.get('key')

        token_util = TokenUtil()
        try:
            # Convert UUID value to String without (-) dashes
            token_id = uuid.UUID(str(key)).hex

            token = token_util.get_token(token_id)
            # Update login status.
            token_util.update_login(token.id, False)

            return Response({"status": status.HTTP_200_OK, "message": token.user.username + " logout!"})

        except (ObjectDoesNotExist, ValidationError, AttributeError, ValueError):
            return Response({"status": status.HTTP_400_BAD_REQUEST, "message": "Invalid token"})


class ClearLoginView(APIView):
    """
    Clear/delete user's login token view for POST request
    """

    def delete(self, request):
        """
        Validate login request a user
        :param request:
        :return: response status and message
        """
        # Get token key
        key = request.data.get('key')
        # Check login details
        username = str(request.data.get('username')).lower()
        password = request.data.get('password')

        # Validate input
        if not key or not username or not password:
            return Response({"status": status.HTTP_404_NOT_FOUND, "message": "Invalid/Incomplete input"})

        token_util = TokenUtil()
        # Validate user token
        token_active = token_util.is_token_login(key)
        login_check = token_util.check_username_and_password(username, password)

        if token_active and login_check:
            try:
                # Delete login token.
                token_data = token_util.delete_token(key)
                return Response({"status": status.HTTP_200_OK,
                                 "message": token_data.user.username + " active login token clear!"})

            except (ObjectDoesNotExist, ValidationError, AttributeError):
                return Response({"status": status.HTTP_400_BAD_REQUEST, "message": "Invalid token"})
        else:
            return Response(TOKEN_NOT_FOUND_INVALID_MSG)


class DepositView(APIView):
    """
    Deposit view to update User deposit account
    """
    def put(self, request, format=None):
        """
        Update a user
        :param format:
        :param request:
        :return: response status and message
        """
        # Check deposit coin
        if not int(request.data.get('deposit')) in ALLOWED_COINS:
            return Response({"status": ALLOWED_COINS_MESSAGE},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Declare utilities and key
        key = request.data.get('key')
        token_util = TokenUtil()
        # Validate user token
        token_expired = token_util.is_token_expired(key)
        token_active = token_util.is_token_login(key)

        if token_expired or not token_active:
            return Response(TOKEN_NOT_FOUND_INVALID_MSG)

        user_data = token_util.get_token(key).user
        # Convert UUID value to String without (-) dashes
        user_id = uuid.UUID(str(user_data.id)).hex

        try:
            user_data = User.objects.get(id=user_id)
            # # Can be use if deposit should be kept
            # user_data.deposit = int(user_data.deposit) + int(request.data.get('deposit'))
            user_data.deposit = int(request.data.get('deposit'))

            user_data.save()
            return Response({"status": "User deposit successful"},
                            status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "User deposit updated failed"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    def patch(self, request, format=None):
        """
        Update a user
        :param format:
        :param pk:
        :param request:
        :return: response status and message
        """
        # Declare utilities and key
        key = request.data.get('key')
        token_util = TokenUtil()
        # Validate user token
        token_expired = token_util.is_token_expired(key)
        token_active = token_util.is_token_login(key)

        if token_expired or not token_active:
            return Response(TOKEN_NOT_FOUND_INVALID_MSG)

        user_data = token_util.get_token(key).user
        # Convert UUID value to String without (-) dashes
        user_id = uuid.UUID(str(user_data.id)).hex

        try:
            user_data = User.objects.get(id=user_id)
            # change = user_data.deposit # Can be use if deposit should be kept
            user_data.deposit = 0

            user_data.save()
            # return Response({"status": "User deposit rest successful", 'data': {'change': change}},
            return Response({"status": "User deposit rest successful"},
                            status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "User deposit updated failed"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    def get(self, request):
        """
        Get Product to a specific User
        :param request:
        :return:
        """
        # Extract data
        username = request.data.get('username')
        key = request.data.get('key')

        # Declare util
        token_util = TokenUtil()
        token = token_util.get_token_by_username(username)

        # Check if any token exist for this user
        token_exist = token_util.token_exist(username)
        token_expired = token_util.is_token_expired(token.key)
        if not token_exist or token_expired:
            return Response({"status": "Session Terminated or Token expired. Please re-login"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Check user role type
        if token.user.role != "BR":
            return Response({"status": "This a Buyer role endpoint"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Validate user token and login status
        token_expired = token_util.is_token_expired(key)
        token_active = token_util.is_token_login(key)
        if token_expired or not token_active:
            return Response(TOKEN_NOT_FOUND_INVALID_MSG)

        try:
            user_data = User.objects.filter(username=username)\
                .values('username', 'role', 'deposit', 'last_updated_datetime')
            return Response({"data": user_data})

        except (ObjectDoesNotExist, IntegrityError):
            return Response({"status": "No User found"},
                            status=status.HTTP_204_NO_CONTENT)


class ProductView(APIView):
    """
    Product View for requests
    """

    def post(self, request):
        """
         Create a user
         :param request:
         :return: response status and message
         """
        print("here")
        # Extract data
        username = request.data.get('username')
        key = request.data.get('key')
        product_name = str(request.data.get('product_name')).upper()
        cost = int(request.data.get('cost'))
        available_amount = request.data.get('available_amount')

        # Check if product name is provided
        if (not product_name or product_name.strip() == "" or product_name == 'NONE') or not cost or not available_amount:
            return Response({"status": '"Product Name", "cost" and "available amount" are required.'},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        if (cost % 5) != 0:
            return Response({"status": "Cost must be divisible by 5"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Declare util
        token_util = TokenUtil()
        token = token_util.get_token_by_username(username)

        # Check if any token exist for this user
        token_exist = token_util.token_exist(username)
        token_expired = token_util.is_token_expired(token.key)
        if not token_exist or token_expired:
            return Response({"status": "Session Terminated or Token expired. Please re-login"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Check user role type
        if token.user.role != "SR":
            return Response({"status": "Only seller user can add product"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Validate user token and login status
        token_expired = token_util.is_token_expired(key)
        token_active = token_util.is_token_login(key)
        if token_expired or not token_active:
            return Response(TOKEN_NOT_FOUND_INVALID_MSG)

        # Check if product name exist
        product_check = Product.objects.filter(product_name=product_name)
        print(product_check)
        if product_check:
            return Response({"status": "Product name exist with a seller"}, status=status.HTTP_406_NOT_ACCEPTABLE)

        # Get User
        seller = token_util.get_user_by_username(request.data.get('username'))
        # Convert UUID value to String without (-) dashes
        user_id = uuid.UUID(str(seller.id)).hex

        try:
            product_data = Product(seller=User.objects.get(id=user_id), product_name=product_name, cost=cost,
                                   available_amount=available_amount)
            product_data.save()
            return Response({"status": "Product creation successful", "data":request.data.dict()},
                            status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            return Response({"status": "Product creation failed"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    def get(self, request):
        """
        Get Product to a specific User
        :param request:
        :return:
        """
        data = {}
        # Extract data
        username = request.data.get('username')
        key = request.data.get('key')

        # Declare util
        token_util = TokenUtil()
        token = token_util.get_token_by_username(username)

        # Check if any token exist for this user
        token_exist = token_util.token_exist(username)
        token_expired = token_util.is_token_expired(token.key)
        if not token_exist or token_expired:
            return Response({"status": "Session Terminated or Token expired. Please re-login"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Check user role type
        if token.user.role != "SR":
            return Response({"status": "Only seller user can add product"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Validate user token and login status
        token_expired = token_util.is_token_expired(key)
        token_active = token_util.is_token_login(key)
        if token_expired or not token_active:
            return Response(TOKEN_NOT_FOUND_INVALID_MSG)

        try:
            product_data = Product.objects.filter(seller__username=username)\
                .values('id', 'product_name', 'cost', 'available_amount', 'last_updated_datetime')
            return Response({"data": product_data})

        except (ObjectDoesNotExist, IntegrityError):
            return Response({"status": "No Product found"},
                            status=status.HTTP_204_NO_CONTENT)

    def put(self, request):
        # Extract data
        username = request.data.get('username')
        key = request.data.get('key')
        product_name = str(request.data.get('product_name')).upper()
        cost = int(request.data.get('cost'))
        available_amount = request.data.get('available_amount')

        # Check if product name is provided
        if (not product_name or product_name.strip() == "" or product_name == 'NONE') or not cost \
                or not available_amount:
            return Response({"status": '"Product Name", "cost" and "available amount" are required.'},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        if cost not in ALLOWED_COINS:
            return Response({"status": ALLOWED_COINS_MESSAGE},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Declare util
        token_util = TokenUtil()
        token = token_util.get_token_by_username(username)

        # Check if any token exist for this user
        token_exist = token_util.token_exist(username)
        token_expired = token_util.is_token_expired(token.key)
        if not token_exist or token_expired:
            return Response({"status": "Session Terminated or Token expired. Please re-login"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Check user role type
        if token.user.role != "SR":
            return Response({"status": "Only seller user can add product"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Validate user token and login status
        token_expired = token_util.is_token_expired(key)
        token_active = token_util.is_token_login(key)
        if token_expired or not token_active:
            return Response(TOKEN_NOT_FOUND_INVALID_MSG)

        # Check if product name exist
        try:
            product_check = Product.objects.filter(product_name=product_name).get()
        except ObjectDoesNotExist:
            return Response({"status": "Product name not found."}, status=status.HTTP_406_NOT_ACCEPTABLE)

        # Check if product name matches
        if product_check.product_name != product_name:
            return Response({"status": "Product name exist with a seller, and can't be changed."},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        try:
            product_data = Product.objects.get(id=product_check.id)
            product_data.cost = cost
            product_data.available_amount = available_amount

            product_data.save()
            return Response({"status": "Product update successful"},
                            status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "Product update failed"}, status=status.HTTP_406_NOT_ACCEPTABLE)

    def delete(self, request):
        """
        Delete a product
        :param request:
        :return:
        """
        # Extract data
        username = request.data.get('username')
        key = request.data.get('key')
        product_name = str(request.data.get('product_name')).upper()

        # Check if product name is provided
        if (not product_name or product_name.strip() == "" or product_name == 'NONE') or not key:
            return Response({"status": '"Product Name" and "Token key" are required.'},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
        # Declare util
        token_util = TokenUtil()
        token = token_util.get_token_by_username(username)

        # Check if any token exist for this user
        token_exist = token_util.token_exist(username)
        token_expired = token_util.is_token_expired(token.key)
        if not token_exist or token_expired:
            return Response({"status": "Session Terminated or Token expired. Please re-login"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Check user role type
        if token.user.role != "SR":
            return Response({"status": "Only seller user can add product"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Validate user token and login status
        token_expired = token_util.is_token_expired(key)
        token_active = token_util.is_token_login(key)
        if token_expired or not token_active:
            return Response(TOKEN_NOT_FOUND_INVALID_MSG)

        # Check if product name exist
        try:
            product_check = Product.objects.filter(product_name=product_name).get()
        except ObjectDoesNotExist:
            return Response({"status": "Product name not found."}, status=status.HTTP_406_NOT_ACCEPTABLE)

        # Check if product name matches
        if product_check.product_name != product_name:
            return Response({"status": "Product name exist with a seller, and can't be changed."},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        try:
            product_data = Product.objects.get(id=product_check.id)

            product_data.delete()
            return Response({"status": "Product deleted successful"},
                            status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": "Product deletion failed"}, status=status.HTTP_406_NOT_ACCEPTABLE)


class BuyView(APIView):
    """
    Buy view for buyer users
    """

    def post(self, request):
        """
         Buy a product
         :param request:
         :return: response status and message
         """
        # Extract data
        username = request.data.get('username')
        product_id = request.data.get('product_id')
        # product_amount = request.data.get('product_amount')
        key = request.data.get('key')

        # if not username or not product_id or not product_amount or not key:
        if not username or not product_id or not key:
            return Response({"status": '"product_id", "product_amount" and "Token key" are required.'},
                            status=status.HTTP_406_NOT_ACCEPTABLE)
        # elif int(product_amount) > 1:
        #     return Response({"status": 'Buyer can only buy a Product at a time.'},
        #                     status=status.HTTP_406_NOT_ACCEPTABLE)
        # Declare util
        token_util = TokenUtil()
        token = token_util.get_token_by_username(username)
        print(token)
        # Check if any token exist for this user
        token_exist = token_util.token_exist(username)
        try:
            token_expired = token_util.is_token_expired(token.key)
        except AttributeError:
            return Response({"status": TOKEN_NOT_FOUND_INVALID_MSG}, status=status.HTTP_406_NOT_ACCEPTABLE)

        if not token_exist or token_expired:
            return Response({"status": "Session Terminated or Token expired. Please re-login"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Check user role type
        if token.user.role != "BR":
            return Response({"status": "Only Buyer user purchase a product"},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        # Validate user token and login status
        token_expired = token_util.is_token_expired(key)
        token_active = token_util.is_token_login(key)
        if token_expired or not token_active:
            return Response(TOKEN_NOT_FOUND_INVALID_MSG)

        # Get Buyer and product data
        buyer_data = token.user
        try:
            product_data = Product.objects.get(id=product_id)
        except ObjectDoesNotExist:
            return Response({"status": "Product not found"}, status=status.HTTP_406_NOT_ACCEPTABLE)

        # Check if buyer has enough money in the account
        buyer_deposit = buyer_data.deposit
        product_cost = product_data.cost
        if buyer_deposit < product_cost:
            return Response({"status": "Sorry, you don't have enough fund. Please deposit fund into your account."},
                            status=status.HTTP_406_NOT_ACCEPTABLE)

        #  Calculate spending and product left
        buyer_balance = buyer_deposit - product_cost
        product_left = product_data.available_amount - 1
        # Calculate change
        count = len(ALLOWED_COINS) - 1
        change = []
        temp_balance = buyer_balance
        while count > 0 or count == 0:
            change_diff = temp_balance - ALLOWED_COINS[count]
            if change_diff > 0 or change_diff == 0:
                change.append(ALLOWED_COINS[count])
                temp_balance = change_diff
            count -= 1
        print(change)
        # Update buyer's account
        try:
            # Convert UUID value to String without (-) dashes
            buyer_id = uuid.UUID(str(buyer_data.id)).hex
            buyer_account = User.objects.get(id=buyer_id)
            # Issue change and reset deposit back to 0
            buyer_account.deposit = 0
            buyer_account.save()

            # Update Product
            product_data.available_amount = product_left
            product_data.save()

            return Response({"data": {"Total Spent": product_data.cost,
                                      "Product purchased": product_data.product_name,
                                      "change": str(change),
                                      }},
                            status=status.HTTP_200_OK)
        except (ObjectDoesNotExist, ValidationError):
            return Response({"status": "Internal Error in updating your account. Please retry or contact support team."},
                            status=status.HTTP_205_RESET_CONTENT)
