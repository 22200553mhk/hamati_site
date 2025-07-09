from django.urls import path
from django.contrib import admin
from analyzer import simple_views  # این خط را اضافه کنید

urlpatterns = [

    path('', simple_views.dashboard, name='dashboard'),
    path('save-result/', simple_views.save_result, name='save_result'),
    path('generate-report/', simple_views.generate_report, name='generate_report'),
]