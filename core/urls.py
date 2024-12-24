from django.urls import path
from .views import *

app_name = 'core'
# whsec_51862af21b9750fc96326363db5e1fb0da34fda49444c65aff06ddef4244796c
urlpatterns = [
    path('', home, name="home"),
    # path('stripe-webhook/', stripe_webhook, name="stripe-webhook"),
    path('login/', login_register_view, name="login_register"),
    path('logout/', logout_view, name="logout"),
    path('reset-password/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('reset-password/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset-password/confirm/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset-password/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('shop/', products, name="products"),
    path('products/', product_list, name='product_list'),
    path('create-product/', create_product, name="create-product"),
    path('product/<slug:product_slug>/', product_details, name='product-details'),
    path('edit-product/<slug:product_slug>/', edit_product, name="edit-product"),
    path('cart/', view_cart, name='view-cart'),
    path('add-to-cart/<slug:product_slug>/', add_to_cart, name='add-to-cart'),
    path('checkout/<int:item_id>', checkout, name='checkout'),
    path('payment/<str:payment_method>/<int:item_id>', payment, name='payment'),
    path('success/', checkout_success, name='success'),
    path('cancel/', checkout_cancel, name='cancel'),
    path('search/', search_view, name='search'),

]
