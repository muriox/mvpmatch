from django.db import models
import uuid
from .constants import ROLES


class User(models.Model):
    """
        USER
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=64, null=False, unique=True)
    password = models.CharField(max_length=256, null=False)
    role = models.CharField(null=False, max_length=5, choices=ROLES)
    deposit = models.IntegerField(default=0)

    last_updated_datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.username) + " - " + str(self.id)


class Product(models.Model):
    """
        PRODUCT
    """
    id = models.AutoField(primary_key=True, editable=False)
    seller = models.ForeignKey(User, on_delete=models.PROTECT, null=False,
                               related_name='Products', related_query_name='Product')
    product_name = models.CharField(max_length=256, null=False, unique=True)
    cost = models.IntegerField(null=False, default=0)
    available_amount = models.IntegerField(null=False)

    last_updated_datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.id) + " - " + str(self.product_name)


class Token(models.Model):
    """
        TOKEN
    """
    id = models.AutoField(primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=False,
                             related_name='Tokens', related_query_name='Token')
    key = models.UUIDField(default=uuid.uuid4, editable=False, auto_created=True)
    login = models.BooleanField(null=False, default=False)
    last_updated_datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(str(self.id) + " - " + str(self.key))
