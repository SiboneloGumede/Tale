from django.urls import path, reverse_lazy
from website import views, forms
from django.contrib.auth import views as auth_views

app_name = 'website'

urlpatterns = [
	path('', views.Landing.as_view(), name='landing'),
	path('our-story/', views.About.as_view(), name='about'),
	path('contact/', views.Contact.as_view(), name='contact'),
	path('terms-and-conditions/', views.Terms.as_view(), name='terms'),
	path('privacy-policy/', views.Privacy.as_view(), name='privacy'),
	path('faqs/', views.FAQ.as_view(), name='faq'),

	path('login/', auth_views.LoginView.as_view(template_name='website/auth/login.html', form_class=forms.LoginForm), name='login'),
    path('signup/', views.signup, name='signup'),
    path('choose-your-pricing-plan/', views.ChoosePlan.as_view(), name='choose-plan'),
	path('password-reset/', auth_views.PasswordResetView.as_view(template_name='website/auth/password_reset_form.html', 
    	email_template_name="website/auth/password_reset_email.html", subject_template_name='website/auth/password_reset_subject.txt', 
    	success_url = reverse_lazy('website:password_reset_email'),
    	from_email="Tale <no-reply@taleapp.io>"), name='password_reset'),
    path('password-reset-email/', auth_views.PasswordResetDoneView.as_view(template_name='website/auth/password_reset_done.html'),
     name='password_reset_email'),
    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(template_name='website/auth/password_reset_confirm.html', 
        	success_url=reverse_lazy('website:password_reset_complete'), form_class=forms.SetPasswordForm), name='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='website/auth/password_reset_complete.html'), 
    	name='password_reset_complete'),
    path('logout/', views.logout_view, name='logout'),

    path('anonymous-login/', views.AnonymousLogin.as_view(), name='anonymous-login'),
    path('anonymous-signup/', views.AnonymousSignup.as_view(), name='anonymous-signup'),

    path('dashboard/', views.Dashboard.as_view(), name='dashboard'),
    path('personal-info/', views.PersonalInfo.as_view(), name='personal-info'),
    path('notifications/', views.Notifications.as_view(), name='notifications'),
    path('security/', views.Security.as_view(), name='security'),
    path('your-orders/', views.YourOrders.as_view(), name='your-orders'),
    path('your-subscriptions/', views.YourSubscriptions.as_view(), name='your-subscriptions'),
    path('your-ebooks/', views.YourEBooks.as_view(), name='your-ebooks'),
    path('your-articles/', views.YourArticles.as_view(), name='your-articles'),
    path('your-orders/invoice/<int:pk>/', views.Invoice.as_view(), name='invoice'),
    path('payments/', views.Payments.as_view(), name='payments'),

    path('authors/<int:pk>/<username>/', views.AuthorSelect.as_view(), name='author-select'),
    path('publications/<int:pk>/<slug>/', views.ArticleSelect.as_view(), name='article-select'),


    path('library/', views.Library.as_view(), name='library'),
    path('tags/<tag>/', views.Tags.as_view(), name='tags'),
    path('pricing/', views.Pricing.as_view(), name='pricing'),
    

    path('cart/', views.Cart.as_view(), name='cart'),
    path('checkout/', views.Checkout.as_view(), name='checkout'),
    path('order-completed/', views.OrderCompleted.as_view(), name='order-completed'),
    path('payment-success/<int:pk>/', views.PaymentSuccess.as_view(), name='payment-success'),
    path('payment-cancel/<int:pk>/', views.PaymentCancel.as_view(), name='payment-cancel'),

    path('add-to-cart/<int:pk>/', views.add_to_cart, name='add-to-cart'),
    path('delete-from-cart/<int:pk>/', views.DeleteFromCart.as_view(), name='delete-from-cart'),

    path('write/<int:pk>/step-1/', views.Step1.as_view(), name='step-1'),
    path('write/<int:pk>/step-2/', views.Step2.as_view(), name='step-2'),
    path('write/<int:pk>/step-3/', views.Step3.as_view(), name='step-3'),
    path('write/<int:pk>/preview/', views.Preview.as_view(), name='preview'),

    path('ajax/write/article/', views.ajax_write_article, name='ajax-write-article'),
    path('ajax/write/ebook/', views.ajax_write_ebook, name='ajax-write-ebook'),
    path('ajax/delete-publication/<int:pk>/', views.ajax_delete_publication, name='ajax-delete-publication'),
    path('ajax/publish-publication/<int:pk>/', views.ajax_publish_publication, name='ajax-publish-publication'),
    path('ajax/pro-upgrade/<int:pk/', views.ProUpgrade.as_view(), name='ajax-pro-upgrade'),
    path('ajax/address-details/<int:pk>/', views.ajax_address_form, name='ajax-address-form'),
    path('ajax/notify/', views.ajax_notify, name='ajax-notify'),
    path('ajax/validate-username/', views.ajax_validate_username, name='ajax-validate-username'),
    path('ajax/article-read/<int:pk>/<int:publication>/', views.ajax_article_read, name='article-read'),
    path('ajax/buy-it-again/<int:pk>/', views.ajax_bia, name='ajax-bia'),
    path('ajax/bookmark-article/<int:pk>/<int:publication>/', views.ajax_bookmark_article, name='ajax-bookmark-article'),
    path('ajax/profile/', views.ajax_profile, name='ajax-profile'),

    path('delete-your-account/<int:pk>/', views.DeleteYourAccount.as_view(), name='delete-your-account'),

    path('users/', views.Users.as_view(), name='users'),
    path('activate-user/<int:pk>/', views.Activate.as_view(), name='activate-user'),
    path('deactivate-user/<int:pk>/', views.Deactivate.as_view(), name='deactivate-user'),
    path('subscriptions/', views.Subscriptions.as_view(), name='subscriptions'),
    path('delete-subscription/<int:pk>/', views.DeleteSub.as_view(), name='delete-subscription'),
    path('content/', views.Content.as_view(), name='content'),
    path('delete-content/<int:pk>/', views.DeleteContent.as_view(), name='delete-content'),
    path('delete-ebook/<int:pk>/', views.DeleteEbook.as_view(), name='delete-ebook'),
    path('delete-article/<int:pk>/', views.DeleteArticle.as_view(), name='delete-article'),

    path('search?q=<word>/', views.Search.as_view(), name='search'),
    path('ajax/search/publication/', views.searchPublication, name='search-publication'),


]