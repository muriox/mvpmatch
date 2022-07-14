from rest_framework import serializers
from .models import *


class UserSerializer(serializers.ModelSerializer):
    """
        User serializer with subclass holding Meta data
    """
    class Meta:
        model = User
        fields = ['username', 'password', 'role', 'deposit', 'last_updated_datetime']
