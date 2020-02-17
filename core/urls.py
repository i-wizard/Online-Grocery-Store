# import path
# import the function from views
from django.urls import path
from .views import (
    HomeView,
    ItemDetailView, 
    CheckoutView, 
    add_to_cart,
    OrderSummaryView,
    remove_from_cart,
    remove_single_item_from_cart,
    add_to_cart_again,
    PaymentView,
    remove_from_cart_again,
    AddCouponView,
    RequestRefundView,
    

)
app_name = "core"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path('product-page/<slug>/.html', ItemDetailView.as_view(), name="products"),
    path('checkout-page.html', CheckoutView.as_view(), name="checkout"),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('add-to-cart/<slug>/.html', add_to_cart, name='add-to-cart'),
    path('add-coupon/', AddCouponView.as_view(), name='add-coupon'),
    path('add-to-cart-again/<slug>/.html', add_to_cart_again, name='add-to-cart-again'), #try
    path('remove-from-cart/<slug>/.html', remove_from_cart, name='remove-from-cart'),
    path('remove-from-cart-again/<slug>/.html', remove_from_cart_again, name='remove-from-cart-again'), #try
    path('remove-item-from-cart/<slug>/.html', remove_single_item_from_cart, name='remove-single-item-from-cart'),
    path('payment/<payment_option>/', PaymentView.as_view(), name='payment'),
    path('request-refund/', RequestRefundView.as_view(), name='request-refund'),
]
# remember to link this urls to the main urls
# ...make the necessary changes at the hom-page.html(change in the forloop)