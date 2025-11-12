from django.urls import path
from website.api import views

app_name = 'api'

urlpatterns = [
    path('webhook/<user>/<author>/', views.WebhookView.as_view(), name='webhook'),
    path('callback/<order>/', views.CallbackView.as_view(), name='callback'),
    path('payment/<user>/', views.PaymentView.as_view(), name='payment')
    
]
