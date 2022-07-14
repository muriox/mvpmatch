from .serializers import *
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.auth.hashers import check_password
from _datetime import datetime
from .constants import TOKEN_NOT_FOUND_INVALID_MSG


class UserUtil:
    """
    User util class
    """
    def check_username_and_password(self, username, password) -> (bool, dict):
        """
        Check/validate user
        :param username:
        :param password:
        :return:
        """

        try:
            # Check if user exist in db
            user_data = User.objects.filter(username=username).get()
            is_valid = check_password(password, user_data.password)

            if is_valid:
                return True
            else:
                return False
        except (ObjectDoesNotExist, ValidationError):
            return {"status": status.HTTP_404_NOT_FOUND, "message": "Invalid Username/Password"}

    def get_user(self, pk):
        """
        Get user by primary key
        :param pk:
        :return:
        """
        try:
            # Return user uuid
            return User.objects.get(id=pk)

        except (ObjectDoesNotExist, ValidationError):
            return {"status": status.HTTP_404_NOT_FOUND, "message": "PK Not Found/Invalid"}

    def get_user_by_username(self, username):
        """
        Get user by their username
        :param username:
        :return:
        """
        try:
            return User.objects.filter(username=username).get()
        except ObjectDoesNotExist:
            # raise status.HTTP_404_NOT_FOUND
            return {"status": status.HTTP_404_NOT_FOUND, "message": "User Not Found/Invalid"}


class TokenUtil(UserUtil):
    """
    Token class for holding all Token functions
    """

    def create_token(self, username):
        """
        Create token
        :param username:
        :return: key
        """
        try:
            user_data = UserUtil.get_user_by_username(self, username)
            # Convert UUID value to String without (-) dashes
            user_id = uuid.UUID(str(user_data.id)).hex
            #
            token_data = Token(user=User.objects.get(id=user_id))
            token_data.save()
            return token_data.key

        except (ObjectDoesNotExist, ValidationError):
            return {"status": status.HTTP_400_BAD_REQUEST, "message": "Token generation FAILED"}
        except AttributeError:
            return {"status": status.HTTP_400_BAD_REQUEST, "message": "Invalid username. Token generation FAILED"}

    def token_exist(self, username):
        """
        Check is user has any active token
        :param username: 
        :return: 
        """
        try:
            token_data = Token.objects.filter(user__username=username)
            print(token_data)
            if token_data:
                return True
            else:
                return False
        except (ObjectDoesNotExist, ValidationError):
            return False

    def get_token(self, key):
        """
        Get token key
        :param key:
        :return:
        """
        # Get token key
        try:
            # Convert UUID value to String without (-) dashes
            key_uuid = uuid.UUID(str(key)).hex

            token_data = Token.objects.filter(key=key_uuid).get()
            return token_data
        except (ObjectDoesNotExist, ValidationError, ValueError, AttributeError):
            return TOKEN_NOT_FOUND_INVALID_MSG

    def get_token_by_username(self, username):
        """
        Get token with username
        :param username:
        :return:
        """
        try:
            token_data = Token.objects.filter(user__username=username).get()
            return token_data
        except (ObjectDoesNotExist, ValidationError):
            return TOKEN_NOT_FOUND_INVALID_MSG

    def get_token_by_key(self, key):
        """
        Get token key
        :param key:
        :return:
        """
        try:
            token_data = self.get_token(key)
            return token_data
        except AttributeError:
            return TOKEN_NOT_FOUND_INVALID_MSG

    def is_token_login(self, key) -> bool:
        """
        Check if token key has expired
        :param key:
        :return:
        """
        try:
            token_data = self.get_token(key)
            print(token_data.login)

            if token_data.login:
                return True
            else:
                return False
        except AttributeError:
            return TOKEN_NOT_FOUND_INVALID_MSG

    def is_token_expired(self, key) -> bool:
        """
        Check if token key has expired
        :param key:
        :return:
        """
        try:
            token_data = self.get_token(key)
            created_time = datetime.strftime(token_data.last_updated_datetime, '%m/%d/%Y %I:%M%p')
            time_now = datetime.strftime(datetime.now(), '%m/%d/%Y %I:%M%p')
            diff = datetime.strptime(time_now, '%m/%d/%Y %I:%M%p') - datetime.strptime(created_time, '%m/%d/%Y %I:%M%p')
            hours = diff.total_seconds() / 36000

            if hours > 1:
                return True
            else:
                return False
        except AttributeError:
            return TOKEN_NOT_FOUND_INVALID_MSG

    def update_login(self, token_id, login) -> bool:
        """
        Update login status
        :param token_id:
        :param login:
        :return:
        """

        token = Token.objects.get(id=token_id)
        token.login = login
        token.save()

        return token.login

    def delete_token(self, key):
        """
        Delete token.
        :param key:
        :return:
        """
        try:
            token_data = self.get_token(key)
            token_data.delete()

            return token_data
        except AttributeError:
            return TOKEN_NOT_FOUND_INVALID_MSG

