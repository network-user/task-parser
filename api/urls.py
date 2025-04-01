from django.urls import path
from .views import (
    get_balance,
    get_token_info, get_balance_batch,
)

urlpatterns = [
    path("balance/<str:address>/", get_balance),
    path("token/info/", get_token_info),
    path("balance/", get_balance_batch)
]