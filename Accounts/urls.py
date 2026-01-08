from django.urls import path
from .views import (
    RegisterView, 
    LoginView, 
    LogoutView, 
    UserProfileView, 
    GoogleAuthView,
    
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # REFRESH LOGIC
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('google/', GoogleAuthView.as_view(), name='google-auth'),
]