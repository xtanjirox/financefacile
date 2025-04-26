import os
from ninja import NinjaAPI
from ninja_extra import NinjaExtraAPI
from django.urls import path
from django.contrib import admin

from .common import router as common_router
from .common import controllers as cart_controllers

api = NinjaExtraAPI()

api.add_router("/", common_router)
api.register_controllers(*cart_controllers)

urlpatterns = [
    path("api/admin/", admin.site.urls),
    path("api/", api.urls),
]
