
from django.urls import path
from . import views
from .api_views import ProductListAPIView

urlpatterns = [
    # HOME
    path('', views.home, name='home'),

    # AUTHENTICATION
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # PRODUCTS
    path('add-product/', views.add_product, name='add_product'),
    path('product/<int:product_id>/', views.product_detail, name='product_detail'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
    path('update-status/<int:product_id>/', views.update_product_status, name='update_product_status'),

    # DASHBOARD AND PROFILE
    path('dashboard/', views.dashboard, name='dashboard'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),

    # API
    path('api/products/', ProductListAPIView.as_view(), name='api_products'),

    # EXCHANGE REQUESTS
    path('send-exchange-request/<int:product_id>/', views.send_exchange_request, name='send_exchange_request'),
    path('exchange-request/<int:request_id>/accept/', views.accept_exchange_request, name='accept_exchange_request'),
    path('exchange-request/<int:request_id>/reject/', views.reject_exchange_request, name='reject_exchange_request'),

    # SELLER REVIEWS
    path('review-seller/<int:exchange_id>/', views.submit_seller_review, name='submit_seller_review'),

    # NOTIFICATIONS
    path('notification/read/<int:notification_id>/', views.mark_notification_read, name='mark_notification_read'),

    # CHAT
    path('chats/', views.chat_list, name='chat_list'),
    path('chat/start/<int:product_id>/', views.start_chat, name='start_chat'),
    path('chat/<int:conversation_id>/', views.chat_room, name='chat_room'),
    path('chat/<int:conversation_id>/send/', views.send_chat_message, name='send_chat_message'),
    path('chat/<int:conversation_id>/fetch/', views.fetch_chat_messages, name='fetch_chat_messages'),

    # WISHLIST
    path('wishlist/', views.my_wishlist, name='my_wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
]
