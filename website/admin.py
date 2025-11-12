from django.contrib import admin
from website import models

# Register your models here.
admin.site.register(models.Contact)
admin.site.register(models.Subscribe)
admin.site.register(models.User)
admin.site.register(models.Order)
admin.site.register(models.Cart)
admin.site.register(models.Publication)
admin.site.register(models.OrderDetail)
admin.site.register(models.AnonymousCart)
admin.site.register(models.Subscription)
admin.site.register(models.ArticleRead)
admin.site.register(models.SavedQuickRead)
admin.site.register(models.SubscriptionPayment)