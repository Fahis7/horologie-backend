from django.urls import path
from .views import (
    RegisterView, 
    LoginView, 
    LogoutView, 
    UserProfileView, 
    GoogleAuthView,
    FirebasePhoneAuthView,
    AdminDashboardStatsView,
    AdminUserListView,
    AdminBlockUserView,
    AdminUpdateRoleView,
    PasswordResetRequestView,
    PasswordResetConfirmView
    
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # REFRESH LOGIC
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('google/', GoogleAuthView.as_view(), name='google-auth'),
    path('firebase/', FirebasePhoneAuthView.as_view(), name='firebase_auth'),
    path('admin/stats/', AdminDashboardStatsView.as_view(), name='admin-stats'),
    
    path('password-reset-request/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
    
    path('admin/users/', AdminUserListView.as_view(), name='admin-users-list'),
    path('admin/users/<int:pk>/block/', AdminBlockUserView.as_view(), name='admin-user-block'),
    path('admin/users/<int:pk>/role/', AdminUpdateRoleView.as_view(), name='admin-user-role'),
]