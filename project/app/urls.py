from django.urls import path
from django.views.generic import TemplateView
from . views import *

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('user_registration/', user_registration, name='user_registration'),
    path('user_login/', user_login, name='user_login'),
    path('logout_user/', logout_user, name='logout_user'),
    path('dashboard/', dashboard, name='dashboard'),
    path('mic/', mic, name='mic'),
    path('upload/', upload, name='upload'),
    path('forgot_pass/', forgot_pass, name='forgot_pass'),
    path('reset_pass/', reset_pass, name='reset_pass'),
    path('setPass/', setPass, name='setPass')
]