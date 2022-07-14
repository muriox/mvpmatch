from django.urls import path
from .views import *
from rest_framework.authtoken.views import obtain_auth_token
from rest_framework.urlpatterns import format_suffix_patterns

urlpatterns = [
    path('', home),
    path('api', api_versions),
    path('api/v1', api_v1),
    path('api/v1/login', LoginView.as_view()),
    path('api/v1/logout', LogoutView.as_view()),
    path('api/v1/logout/all', ClearLoginView.as_view()),
    path('api/v1/reset', LoginView.as_view()),
    path('api/v1/user', UserView.as_view()),
    path('api/v1/product', ProductView.as_view()),
    path('api/v1/deposit', DepositView.as_view()),
    path('api/v1/deposit/rest', DepositView.as_view()),
    path('api/v1/buy', BuyView.as_view()),
    path('api/tests', test),
]

# urlpatterns = format_suffix_patterns(urlpatterns)

