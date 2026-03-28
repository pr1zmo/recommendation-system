"""
URL configuration for recommendation project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from recommendation.views import bootstrap, data_json, event_action, home, login_view, logout_view, recommend_view, update_preferences

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/bootstrap', bootstrap, name='bootstrap'),
    path('api/login', login_view, name='login'),
    path('api/logout', logout_view, name='logout'),
    path('api/events/<str:event_id>/action', event_action, name='event-action'),
    path('api/user/preferences', update_preferences, name='update-preferences'),
    path('api/recommendations', recommend_view, name='recommendations'),
    path('data.json', data_json, name='data-json'),
    path('', home, name='home'),
]
