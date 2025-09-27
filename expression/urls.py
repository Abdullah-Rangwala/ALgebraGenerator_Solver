from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    path('', auth_views.LoginView.as_view(template_name='expression/login.html'), name='login'),  # Root URL points to login
    path('home/', views.home, name='home'),  # Algebra Solver home page
    path('login/', auth_views.LoginView.as_view(template_name='expression/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('generate/', views.generate_equation, name='generate'),
    path('solve/', views.solve_equation, name='solve'),
    path('history/', views.get_history, name='history'),
    path('clear-history/', views.clear_history, name='clear_history'),
]