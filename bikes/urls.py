from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),  # ✅ here is the "search" url
    path("buy-bike/", views.buy_bike, name="buy_bike"),
     path('contact/', views.contact_view, name='contact'),
    
    # AJAX validation endpoint
    path('validate/', views.validate_contact_field, name='validate_field'),
    
    # API endpoint
    path('api/', views.ContactAPIView.as_view(), name='api'),
    
    # Admin dashboard (requires staff permissions)
    path('dashboard/', views.contact_dashboard, name='dashboard'),
    
    # Bulk actions (admin)
    path('bulk-update/', views.bulk_update_submissions, name='bulk_update'),

    path("auth/", views.auth_view, name="auth"),

    path("about/", views.about, name="about"),
 
    path('sell_motorcycle/', views.sell_motorcycle, name='sell_motorcycle'),
     path('bike/<int:id>/', views.bike_detail, name='bike_detail'),


]
