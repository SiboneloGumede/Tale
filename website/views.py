from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from website import models, forms
from django.contrib.auth import login, logout
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
import requests, urllib.parse, hashlib, calendar, random, os
from website.payfast import dataToString, passPhrase, generatePaymentIdentifier, generateSignature
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.contenttypes.models import ContentType
from django.db.models.functions import TruncMonth, ExtractMonth
from django.db.models import Count, Sum
from website.functions import Month
from website.api.views import f
from sendgrid import SendGridAPIClient
from django.contrib.postgres.search import SearchVector

sg = SendGridAPIClient(api_key='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')

'''BEGIN AUTH VIEWS'''
def logout_view(request):
    logout(request)
    return redirect('website:login')

def handler404(request, exception):
    return render(request, 'website/404.html', status=404)

def handler403(request, exception):
    return render(request, 'website/403.html', status=403)

def handler500(request):
    return render(request, 'website/500.html', status=500)

def ajax_validate_username(request):
    username = request.GET.get('username', None)
    data = {
        'is_taken': models.User.objects.filter(username__iexact=username).exists()
    }
    
    return JsonResponse(data)

def signup(request):
    is_anonymous = False
    if request.method == 'POST':
        form = forms.SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 2
            user.account_type = 1
            user.gender = 1
            user.first_name = request.POST.get('first_name', '')
            user.last_name = request.POST.get('last_name', '')
            user.save()

            new_account = render_to_string('website/email/new-account.html', {'name': user.first_name})

            send_mail(
                subject='[Tale] %s, Welcome to Tale' % (user.first_name),
                message='',
                from_email='no-reply@taleapp.io',
                recipient_list=[
                user.email,
                ],
                html_message=new_account,
                )

            login(request, user)

            try:
                data = {"contacts": [{"email": user.email,
                "first_name": user.first_name, "last_name": user.last_name}]}

                response = sg.client.marketing.contacts.put(
                    request_body=data
                )
            except Exception:
                pass

            return redirect('website:choose-plan')
    else:
        form = forms.SignUpForm()
    return render(request, 'website/auth/signup.html', {'form': form,
        'is_anonymous': is_anonymous})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class ChoosePlan(View):
    def get(self, request):
        myData = {
            'merchant_id':'17547784',
            'merchant_key': 'f94fol0ztgcrc',
            'return_url': 'https://www.taleapp.io/pricing/',
            'cancel_url': 'https://www.taleapp.io/pricing/',
            'notify_url': 'https://www.taleapp.io/api/payment/{}/'.format(f.encrypt(str(request.user.pk).encode('utf-8'))),
            'email_address': request.user.email,
            'amount': "79",
            'item_name': 'Tale Pro Plan Subscription',
            'subscription_type': '1',
            'recurring_amount': "79",
            'frequency': '3',
            'cycles': '0',
            
        }
        
        myData["signature"] = generateSignature(myData, passPhrase)
        pfParamString = dataToString(myData, passPhrase);
        monthly_identifier = generatePaymentIdentifier(pfParamString);

        myData = {
            'merchant_id':'17547784',
            'merchant_key': 'f94fol0ztgcrc',
            'return_url': 'https://www.taleapp.io/pricing/',
            'cancel_url': 'https://www.taleapp.io/pricing/',
            'notify_url': 'https://www.taleapp.io/api/payment/{}/'.format(f.encrypt(str(request.user.pk).encode('utf-8'))),
            'email_address': request.user.email,
            'amount': "853",
            'item_name': 'Tale Pro Plan Subscription',
            'subscription_type': '1',
            'recurring_amount': "853",
            'frequency': '6',
            'cycles': '0',
            
        }
        
        myData["signature"] = generateSignature(myData, passPhrase)
        pfParamString = dataToString(myData, passPhrase);
        yearly_identifier = generatePaymentIdentifier(pfParamString);
        return render(request, 'website/auth/signup-2.html', {'request': request, 
            'monthly_identifier': monthly_identifier, 'yearly_identifier': yearly_identifier})

    def post(self, request):
        user = request.user
        account_type = request.POST.get('account_type', '0')
        user.account_type = (int(account_type))
        user.save()

        return JsonResponse({'200': 'success'})

class AnonymousLogin(View):
    def get(self, request):
        is_anonymous = True
        if request.user.is_authenticated:
            return redirect('website:checkout')
        
        cart = models.AnonymousCart.objects.get(user=request.COOKIES['cart_id'])

        return render(request, 'website/auth/login.html', {'request': request, 
            'cart': cart, 'form': forms.AuthenticationForm, 'is_anonymous': is_anonymous})

    def post(self, request):
        cart = models.AnonymousCart.objects.get(user=request.COOKIES['cart_id'])
        form = forms.AuthenticationForm(data=request.POST)

        if form.is_valid():

            login(request, form.get_user())
            for order_detail in cart.order_details.all():
                if not request.user.cart_set.first().order_details.filter(publication=order_detail.publication).exists():
                    order_detail.content_object =  request.user.cart_set.first()
                    order_detail.save()
            print('done')
            cart.delete()

            return redirect('website:checkout')
        else:
            messages.error(request, form.errors)
            return redirect('website:anonymous-login')

class AnonymousSignup(View):
    def get(self, request):
        
        is_anonymous = True

        if request.user.is_authenticated:
            return redirect('website:checkout')
        try:
            cart = models.AnonymousCart.objects.get(user=request.COOKIES['cart_id'])
        except Exception:
            return redirect('website:anonymous-signup')

        return render(request, 'website/auth/signup.html', {'request': request, 
            'cart': cart, 'form': forms.SignUpForm, 'is_anonymous': is_anonymous})

    def post(self, request):
        cart = models.AnonymousCart.objects.get(user=request.COOKIES['cart_id'])
        form = forms.SignUpForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.user_type = 2
            user.account_type = 1
            user.gender = 1
            user.save()

            new_account = render_to_string('website/email/new-account.html', {'name': user.first_name})

            send_mail(
                subject='[Tale] %s, Welcome to Tale' % (user.first_name),
                message='',
                from_email='no-reply@taleapp.io',
                recipient_list=[
                user.email,
                ],
                html_message=new_account,
            )

            login(request, user)

            for order_detail in cart.order_details.all():
                order_detail.content_object =  request.user.cart_set.first()
                order_detail.save()

            cart.delete()

            try:
                data = {"contacts": [{"email": user.email,
                "first_name": user.first_name, "last_name": user.last_name}]}

                response = sg.client.marketing.contacts.put(
                    request_body=data
                )
            except Exception:
                pass

            return redirect('website:checkout')
        messages.error(request, form.errors)
        print(form.errors)
        
        return redirect('website:anonymous-signup')

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class DeleteYourAccount(View):
    def post(self, request, pk):
        try:
            user = models.User.objects.get(pk=pk)
            user.is_active = False
            user.save()
            messages.success(request, "Your account has been successfully deleted. Please contact us within 14 days should you wish to recover your account.")
            return redirect('website:login')
        except Exception:
            messages.error(request, "Something went wrong while trying to delete your account. Please try again.")
            return redirect('website:personal-info')


'''END AUTH VIEWS'''

'''BEGIN AJAX VIEWS'''
@login_required
def ajax_write_article(request):
    publication = models.Publication(user=request.user, amount=0, publication_type='Article')
    publication.save()
    return redirect('website:step-1', publication.pk)

@login_required
def ajax_write_ebook(request):
    publication = models.Publication(user=request.user, amount=0, publication_type='eBook')
    publication.save()
    return redirect('website:step-1', publication.pk)

@login_required
def ajax_delete_publication(request, pk):
    publication = models.Publication.objects.get(pk=pk)
    publication.delete()
    return redirect('website:landing')

@login_required
def ajax_publish_publication(request, pk):
    publication = models.Publication.objects.get(pk=pk)
    publication.is_published = True
    publication.save()
    subscribers = models.Subscription.objects.filter(author=publication.user).filter(is_active=True)

    for subscriber in subscribers:
        if subscriber.subscriber.has_notifications:
            new_article = render_to_string('website/email/new-article.html', {'author': subscriber.author.get_full_name(),
                'link': 'https://www.taleapp.io/publications/{}/{}/'.format(publication.pk, publication.slug()),
                'name': subscriber.subscriber.first_name})

            send_mail(
                subject='[Tale] {} has published a new article'.format(subscriber.author.get_full_name()),
                message='',
                from_email='no-reply@taleapp.io',
                recipient_list=[
                subscriber.subscriber.email,
                ],
                html_message=new_article,
            )
    return redirect('website:article-select', publication.pk, publication.slug())

@login_required
def ajax_address_form(request, pk):
    user = models.User.objects.get(pk=pk)

    try:
        user.country = request.POST.get('country', '')
        user.address_line_1 = request.POST.get('address_line_1', '')
        user.address_line_2 = request.POST.get('address_line_2', '')
        user.city = request.POST.get('city', '')
        user.province = request.POST.get('province', '')
        user.postal_code = request.POST.get('postal_code', '')
        user.save()
        messages.success(request, "Address details updated successfully.", extra_tags='personal-info')

        return redirect('website:personal-info')
    except Exception:
        messages.error(request, "Something went wrong while trying to update your address details. Please try again", extra_tags='personal-info')
        return redirect('website:personal-info')

@login_required
def ajax_notify(request):
    user = request.user
    checked = request.POST.get('checked', 'on')
    if checked == 'on':
        user.has_notifications = True
    else:
        user.has_notifications = False
    user.save()
    return JsonResponse({'checked': checked})

@login_required
def ajax_article_read(request, pk, publication):
    user = request.user
    ar = models.ArticleRead(user=user, publication=models.Publication.objects.get(pk=publication))
    ar.save()
    return JsonResponse({'200': ar.__str__()})

@login_required
def ajax_bia(request, pk):
    user = request.user
    cart = user.cart_set.first()
    order = models.Order.objects.get(pk=pk)
    for od in order.order_details.all():
        cd = models.OrderDetail(content_object=cart,
            publication=od.publication, quantity=1)
        cd.save()
    return redirect('website:cart')
    
@login_required
def ajax_bookmark_article(request, pk, publication):
    user = models.User.objects.get(pk=pk)
    publication = models.Publication.objects.get(pk=publication)

    exists = models.SavedQuickRead.objects.filter(user=user).filter(publication=publication).exists()
    
    if not exists:
        sqr = models.SavedQuickRead(user=user, publication=publication)
        sqr.save()
    else:
        sqr = models.SavedQuickRead.objects.filter(user=user).filter(publication=publication).first()
    return JsonResponse({'200': sqr.__str__()})

@login_required
def ajax_profile(request):
    user = request.user
    return redirect('website:author-select', user.pk, user.username)
'''END AJAX VIEWS'''

class Landing(View):
    def get(self, request):
        publications = models.Publication.objects.filter(is_published=True).order_by('-date')
        
        paginator = Paginator(publications, 7)
        page = request.GET.get('page')
        publications = paginator.get_page(page)
        

        tags = []
        for tag in models.Publication.objects.values_list('tags', flat=True):
            tags += tag.split(', ')

        tags = list(filter(None, tags))

        authors = []

        for publication in publications:
            authors.append(publication.user)

        latest_publications = publications[:3]

        return render(request, 'website/index.html',
    	{'request': request, 'publications': publications,
        'range': range(publications.paginator.num_pages), 'tags': set(tags),
        'authors': set(authors), 'latest_publications': latest_publications})

    def post(self, request):
        email = request.POST.get('email', '')

        subscriber = models.Subscribe(email=email)
        subscriber.save()

        try:
            data = {"contacts": [{"email": email}]}

            response = sg.client.marketing.contacts.put(
                request_body=data
            )
        except Exception:
            pass

        return JsonResponse({'email':email})

class About(View):
	def get(self, request):
		return render(request, 'website/about.html',
			{'request': request})

class Contact(View):
    def get(self, request):
    	return render(request, 'website/contact.html',
    		{'request': request})

    def post(self, request):
        name = "%s %s" % (request.POST.get('first_name', ''), request.POST.get('last_name', ''))
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        message = request.POST.get('message', '')
        try:
            check = int(request.POST.get('check', '0'))

            if check == 22:

                contact = models.Contact(name=name,
                	email=email, phone=phone,
                	message=message)
                contact.save()

                html = 'Dear Tale,<br><br>Please see the following contact form submission:<br>Name: {}<br>Email: {}<br>Phone: {}<br>Message:{}<br><br>Regards,<br>The Airos Team'.format(name, 
                    email, phone, message)

                send_mail('[Website] Contact Form Submission - {}'.format(name), '', 'no-reply@taleapp.io', 
                    ['admin@taleapp.io',], fail_silently=False, html_message=html)

                try:
                    data = {"contacts": [{"email": email,
                    "first_name": request.POST.get('first_name', ''), 
                    "last_name": request.POST.get('last_name', '')}]}

                    response = sg.client.marketing.contacts.put(
                        request_body=data
                    )
                except Exception:
                    pass
        except Exception:
            pass


        return JsonResponse({'name':name})

class Terms(View):
    def get(self, request):
        return render(request, 'website/terms.html',
            {'request': request})

class Privacy(View):
    def get(self, request):
        return render(request, 'website/privacy.html',
            {'request': request})

class FAQ(View):
    def get(self, request):
        return render(request, 'website/faq.html',
            {'request': request})

class AuthorSelect(View):
    def get(self, request, pk, username):
        author = models.User.objects.get(pk=pk)
        is_mine = author.pk == request.user.pk

        paginator = Paginator(author.publications().filter(publication_type='Article').filter(is_published=True), 6)
        page = request.GET.get('page')
        publications = paginator.get_page(page)

        if request.user.is_authenticated:
            user = request.user
            is_subscribed = models.Subscription.objects.filter(subscriber=user).filter(author=author).filter(is_active=True).exists()

            if not is_subscribed:
                myData = {
                    'merchant_id':'17547784',
                    'merchant_key': 'f94fol0ztgcrc',
                    'return_url': 'https://www.taleapp.io/authors/{}/{}/'.format(author.pk, author.username),
                    'cancel_url': 'https://www.taleapp.io/authors/{}/{}/'.format(author.pk, author.username),
                    'notify_url': 'https://www.taleapp.io/api/webhook/{}/{}/'.format(f.encrypt(str(request.user.pk).encode('utf-8')), 
                        f.encrypt(str(author.pk).encode('utf-8'))),
                    'email_address': request.user.email,
                    'amount': "{:.0f}".format(author.amount),
                    'item_name': 'Tale Subscription to {}'.format(author.get_full_name()),
                    'subscription_type': '1',
                    'recurring_amount': "{:.0f}".format(author.amount),
                    'frequency': '3',
                    'cycles': '0',
                    
                }

                setup = 'merchant_id={}&percentage50'.format(author.merchant_id)
                

                myData["signature"] = generateSignature(myData, passPhrase)
                myData['setup'] = setup
                pfParamString = dataToString(myData, passPhrase);
                identifier = generatePaymentIdentifier(pfParamString);
            else:
                identifier = ''
                is_subscribed = True


        else:
            identifier = ''
            is_subscribed = False

        subscribers = models.Subscription.objects.filter(author=author).filter(is_active=True).count()
        subscriptions = models.Subscription.objects.filter(subscriber=author).filter(is_active=True).count()
        ebooks = models.Publication.objects.filter(user=author).filter(publication_type='eBook').filter(is_published=True)

        return render(request, 'website/author-select.html',
            {'request': request, 'author': author, 
            'publications': publications,
            'range': range(publications.paginator.num_pages),
            'identifier': identifier, 
            'is_subscribed': is_subscribed,
            'subscribers': subscribers,
            'subscriptions': subscriptions,
            'ebooks': ebooks,
            'is_mine': is_mine})

class ArticleSelect(View):
    def get(self, request, pk, slug):
        article = models.Publication.objects.get(pk=pk)
        related_articles = article.user.publications().exclude(pk=article.pk).order_by('-date')[:4]
        
        if request.user.is_authenticated:
            user = request.user
            is_subscribed = models.Subscription.objects.filter(subscriber=user).filter(author=article.user).filter(is_active=True).exists()

            if not is_subscribed:
                myData = {
                    'merchant_id':'17547784',
                    'merchant_key': 'f94fol0ztgcrc',
                    'return_url': 'https://www.taleapp.io/publications/{}/{}/'.format(article.pk, article.slug()),
                    'cancel_url': 'https://www.taleapp.io/publications/{}/{}/'.format(article.pk, article.slug()),
                    'notify_url': 'https://www.taleapp.io/api/webhook/{}/{}/'.format(f.encrypt(str(request.user.pk).encode('utf-8')), 
                        f.encrypt(str(article.user.pk).encode('utf-8'))),
                    'email_address': request.user.email,
                    'amount': "{:.0f}".format(article.user.amount),
                    'item_name': 'Tale Subscription to {}'.format(article.user.get_full_name()),
                    'subscription_type': '1',
                    'recurring_amount': "{:.0f}".format(article.user.amount),
                    'frequency': '3',
                    'cycles': '0',
                    
                }

                setup = 'merchant_id={}&percentage50'.format(article.user.merchant_id)
                

                myData["signature"] = generateSignature(myData, passPhrase)
                myData['setup'] = setup
                pfParamString = dataToString(myData, passPhrase);
                identifier = generatePaymentIdentifier(pfParamString);
            else:
                identifier = ''

        else:
            is_subscribed = False
            identifier = ''

        tags = article.tags.split(', ')
        tags = list(filter(None, tags))

        return render(request, 'website/article-select.html',
            {'request': request, 'article': article, 
            'related_articles': related_articles, 'is_subscribed': is_subscribed,
            'identifier': identifier, 'tags': set(tags)})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Library(View):
    def get(self, request):
        user = request.user
        sqrs = user.savedquickread_set.order_by('date')
        ebooks = models.OrderDetail.objects.filter(order__user=user).filter(order__status='Paid')
        drafts = user.publication_set.filter(is_published=False)
        return render(request, 'website/library.html',
            {'request': request, 'sqrs': sqrs, 'ebooks': ebooks, 'drafts': drafts})

class Tags(View):
    def get(self, request, tag):
        publications = models.Publication.objects.filter(is_published=True).filter(tags__contains=tag)
        paginator = Paginator(publications, 7)
        page = request.GET.get('page')
        publications = paginator.get_page(page)

        tags = []
        for tag in models.Publication.objects.values_list('tags', flat=True):
            tags += tag.split(', ')

        tags = list(filter(None, tags))

        authors = []

        for publication in publications:
            authors.append(publication.user)

        return render(request, 'website/tags.html',
        {'request': request, 'publications': publications,
        'range': range(publications.paginator.num_pages), 'tags': set(tags),
        'authors': set(authors)})


class Pricing(View):
    def get(self, request):
        if request.user.is_authenticated:
            myData = {
                'merchant_id':'17547784',
                'merchant_key': 'f94fol0ztgcrc',
                'return_url': 'https://www.taleapp.io/pricing/',
                'cancel_url': 'https://www.taleapp.io/pricing/',
                'notify_url': 'https://www.taleapp.io/api/payment/{}/'.format(f.encrypt(str(request.user.pk).encode('utf-8'))),
                'email_address': request.user.email,
                'amount': "79",
                'item_name': 'Tale Pro Plan Subscription',
                'subscription_type': '1',
                'recurring_amount': "79",
                'frequency': '3',
                'cycles': '0',
                
            }
            
            myData["signature"] = generateSignature(myData, passPhrase)
            pfParamString = dataToString(myData, passPhrase);
            monthly_identifier = generatePaymentIdentifier(pfParamString);

            myData = {
                'merchant_id':'17547784',
                'merchant_key': 'f94fol0ztgcrc',
                'return_url': 'https://www.taleapp.io/pricing/',
                'cancel_url': 'https://www.taleapp.io/pricing/',
                'notify_url': 'https://www.taleapp.io/api/payment/{}/'.format(f.encrypt(str(request.user.pk).encode('utf-8'))),
                'email_address': request.user.email,
                'amount': "853",
                'item_name': 'Tale Pro Plan Subscription',
                'subscription_type': '1',
                'recurring_amount': "853",
                'frequency': '6',
                'cycles': '0',
                
            }
            
            myData["signature"] = generateSignature(myData, passPhrase)
            pfParamString = dataToString(myData, passPhrase);
            yearly_identifier = generatePaymentIdentifier(pfParamString);


        else:
            monthly_identifier = ''
            yearly_identifier = ''

        return render(request, 'website/pricing.html',
            {'request': request, 'monthly_identifier': monthly_identifier,
            'yearly_identifier': yearly_identifier})

class Cart(View):
    def get(self, request):
        if request.user.is_authenticated:
            cart = request.user.cart_set.first()
        else:
            try:
                cart = models.AnonymousCart.objects.get(user=request.COOKIES['cart_id'])
            except Exception:
                cart = models.AnonymousCart(user=request.COOKIES['cart_id'])
                cart.save()

        return render(request, 'website/cart.html',
            {'request': request, 'cart': cart, 
            'order_details': cart.order_details, 'count': cart.order_details.count()})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Checkout(View):
    def get(self, request):
        user = request.user
        cart = user.cart_set.first()

        if cart.is_empty():
            return redirect('website:cart')
        
        myData = {
            'merchant_id':'17547784',
            'merchant_key': 'f94fol0ztgcrc',
            'email_address': user.email,
            'cell_number': '0730245763',
            'amount': "{:.0f}".format(cart.total_value_nonlocale()),
            'item_name': 'Tale',
            'subscription_type': '1',
            'recurring_amount': "{:.0f}".format(cart.total_value_nonlocale()),
            'frequency': '3',
            'cycles': '0',
            
        }        

        myData["signature"] = generateSignature(myData, passPhrase)
        pfParamString = dataToString(myData, passPhrase);
        identifier = generatePaymentIdentifier(pfParamString);

        return render(request, 'website/checkout.html',
            {'request': request, 'cart': cart, 
            'order_details': cart.order_details, 'user': user,
            'uform': forms.UserForm(instance=user), 'count': cart.order_details.count(),
            'identifier': identifier})

    def post(self, request):
        user = request.user
        uform = forms.UserForm(request.POST, instance=user)
        cart = user.cart_set.first()

        if uform.is_valid():
            uform = uform.save(commit=False)
            uform.save()

            order = models.Order(user=user)
            order.save()

            for order_detail in cart.order_details.all():
                order_detail.content_object = order
                order_detail.save()

            placed = render_to_string('website/email/order-complete.html', {'name': user.first_name, 
            'order': order, 'order_details': order.order_details})

            send_mail(
                subject='[Tale] Your order has been placed.',
                message='',
                from_email='no-reply@taleapp.io',
                recipient_list=[
                user.email,
                ],
                html_message=placed,
                )

            placed_tale = render_to_string('website/email/order-complete-tale.html', {'name': user.get_full_name(), 
                'order': order, 'order_details': order.order_details, 
                'link': 'https://www.taleapp.io/order/{}'.format(order.id)})

            send_mail(
                subject='[Website] An order has been placed.',
                message='',
                from_email='no-reply@taleapp.io',
                recipient_list=[
                'admin@airos.co.za', 
                ],
                html_message=placed_tale,
                )

            return JsonResponse({'200': 'success', 'pk': order.pk})

        return JsonResponse({'400': 'bad request'})


class OrderCompleted(View):
    def get(self, request):
        return render(request, 'website/order-completed.html',
            {'request': request})


'''BEGIN CART VIEWS'''

def add_to_cart(request, pk):
    if request.user.is_authenticated:
        cart = request.user.cart_set.first()
    else:
        try:
            cart = models.AnonymousCart.objects.get(user=request.COOKIES['cart_id'])
        except Exception:
            cart = models.AnonymousCart(user=request.COOKIES['cart_id'])
            cart.save()

    publication = models.Publication.objects.get(pk=pk)

    if not cart.order_details.filter(publication=publication).exists():
        order_detail = models.OrderDetail(content_object=cart, publication=publication, 
            amount=publication.amount, quantity=1)
        order_detail.save()

    return redirect('website:cart')

class DeleteFromCart(View):
    def get(self, request, pk):
        order_detail = models.OrderDetail.objects.get(pk=pk)
        order_detail.delete()

        return redirect('website:cart')
'''END CART VIEWS'''

'''BEGIN PORTAL VIEWS'''
@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Dashboard(View):
    def get(self, request):
        user = request.user

        '''BEGIN EBOOK SALES'''
        order_type = ContentType.objects.get(app_label='website', model='order')
        ebook_sales = models.OrderDetail.objects.filter(publication__user=user).filter(content_type=order_type).filter(order__status='Paid')
        ebook_sales = ebook_sales.annotate(m=Month('order__placed')).values('m').annotate(total=Sum('quantity'))
        ebook_values = []
        for sale in ebook_sales:
            ebook_values.append([sale['m'], sale['total']])

        for value in ebook_values[1:]:
            prev = ebook_values[ebook_values.index(value) - 1][0]

            if prev + 1 != value[0]:
                ebook_values.append([prev + 1, 0])

        ebook_values = sorted(ebook_values, key=lambda x: x[0], reverse=False)

        ebook_labels = []
        ebook_data = []
        
        for value in ebook_values:
            ebook_labels.append(calendar.month_abbr[value[0]])
            ebook_data.append(value[1])
        '''END EBOOK SALES'''

        '''BEGIN ARTICLE READS'''

        article_reads = models.ArticleRead.objects.filter(publication__user=user)
        article_reads = article_reads.annotate(m=Month('date')).values('m').annotate(num_reads=Sum('quantity'))

        article_values = []
        for read in article_reads:
            article_values.append([read['m'], read['num_reads']])

        for value in article_values[1:]:
            prev = article_values[article_values.index(value) - 1][0]

            if prev + 1 != value[0]:
                article_values.append([prev + 1, 0])

        article_values = sorted(article_values, key=lambda x: x[0], reverse=False)

        article_labels = []
        article_data = []
        
        for value in article_values:
            article_labels.append(calendar.month_abbr[value[0]])
            article_data.append(value[1])
        '''END ARTICLE READS'''

        '''BEGIN SUBSCRIBERS'''
        subscribers = models.Subscription.objects.filter(author=user).filter(is_active=True)
        subscribers = subscribers.annotate(m=Month('date')).values('m').annotate(num_subscriptions=Sum('quantity'))

        subscriber_values = []
        for sub in subscribers:
            subscriber_values.append([sub['m'], sub['num_subscriptions']])

        for value in subscriber_values[1:]:
            prev = subscriber_values[subscriber_values.index(value) - 1][0]

            if prev + 1 != value[0]:
                subscriber_values.append([prev + 1, 0])

        subscriber_values = sorted(subscriber_values, key=lambda x: x[0], reverse=False)

        subscriber_labels = []
        subscriber_data = []
        
        for value in subscriber_values:
            subscriber_labels.append(calendar.month_abbr[value[0]])
            subscriber_data.append(value[1])
        '''END SUBSCRIBERS'''


        return render(request, 'website/portal/dashboard.html',
            {'request': request, 'user': user,
            'uform': forms.UserForm(instance=user), 'ebook_labels': ebook_labels,
            'ebook_data': ebook_data, 'article_labels': article_labels,
            'article_data': article_data, 'subscriber_labels': subscriber_labels,
            'subscriber_data': subscriber_data})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class PersonalInfo(View):
    def get(self, request):
        user = request.user
        print(user.is_zero(), user.is_pro())
        return render(request, 'website/portal/personal-info.html',
            {'request': request, 'user': user,
            'uform': forms.UserForm(instance=user),
            'pform': forms.ProfilePhotoForm(instance=user)})

    def post(self, request):
        user = request.user
        uform = forms.UserForm(request.POST, instance=user)
        pform = forms.ProfilePhotoForm(request.POST, request.FILES, instance=user)

        if pform.is_valid():
            try:
                pform.save()
                messages.success(request, "Personal info updated successfully.", extra_tags='personal-info')
            except AttributeError:
                pass

        if uform.is_valid():
            uform = uform.save(commit=False)
            uform.gender = request.POST.get('gender', 1)
            uform.bio = request.POST.get('bio', '')
            merchant_id = request.POST.get('merchant_id', 0)
            if merchant_id:
                uform.merchant_id = merchant_id
            uform.save()
            messages.success(request, "Personal info updated successfully.", extra_tags='personal-info')


            return redirect('website:personal-info')

        # messages.error(request, "Something went wrong while trying to update your personal info. Please try again", extra_tags='personal-info')

        return redirect('website:personal-info')

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Notifications(View):
    def get(self, request):
        return render(request, 'website/portal/notifications.html',
            {'request': request, 'user': request.user})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Security(View):
    def get(self, request):
        return render(request, 'website/portal/security.html',
            {'request': request, 'user': request.user})

    def post(self, request):
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            messages.success(request, "Your password has been changed successfully")
            return redirect('website:security')
        else:
            messages.error(request, form.errors)
            return redirect('website:security')

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class YourOrders(View):
    def get(self, request):
        user = request.user
        closed_orders = user.order_set.filter(status='Paid')
        open_orders = user.order_set.filter(status='Awaiting Payment')

        paginator = Paginator(closed_orders, 3)
        page = request.GET.get('page')
        closed_orders = paginator.get_page(page)

        return render(request, 'website/portal/your-orders.html',
            {'request': request, 'user': user, 'closed_orders': closed_orders,
            'open_orders': open_orders, 'range': range(closed_orders.paginator.num_pages),})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Invoice(View):
    def get(self, request, pk):
        user = request.user
        order = models.Order.objects.get(pk=pk)

        return render(request, 'website/portal/invoice.html',
            {'request': request, 'user': user, 'order': order})


@method_decorator([login_required(login_url='website:login')], name='dispatch')
class YourSubscriptions(View):
    def get(self, request):
        user = request.user
        subscriptions = models.Subscription.objects.filter(subscriber=user).order_by('date')
        return render(request, 'website/portal/your-subscriptions.html',
            {'request': request, 'user': user, 'subscriptions': subscriptions})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class YourEBooks(View):
    def get(self, request):
        user = request.user
        ebooks = models.Publication.objects.filter(user=user).filter(publication_type='eBook').filter(is_published=True)
        return render(request, 'website/portal/your-ebooks.html',
            {'request': request, 'user': user, 'ebooks': ebooks})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class YourArticles(View):
    def get(self, request):
        user = request.user
        articles = models.Publication.objects.filter(user=user).filter(publication_type='Article').filter(is_published=True)
        return render(request, 'website/portal/your-articles.html',
            {'request': request, 'user': user, 'articles': articles})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Payments(View):
    def get(self, request):
        user = request.user
        payments = user.subscriptionpayment_set.order_by('-date')
        return render(request, 'website/portal/payments.html',
            {'request': request, 'user': user, 'payments': payments})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Users(View):
    def get(self, request):
        user = request.user
        users = models.User.objects.all()
        return render(request, 'website/portal/users.html',
            {'request': request, 'user': user,
            'users': users})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Subscriptions(View):
    def get(self, request):
        user = request.user
        subscriptions = models.Subscription.objects.order_by('-date')
        return render(request, 'website/portal/subscriptions.html',
            {'request': request, 'user': user,
            'subscriptions': subscriptions})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Content(View):
    def get(self, request):
        user = request.user
        publications = models.Publication.objects.filter(is_published=True).order_by('-date')
        return render(request, 'website/portal/content.html',
            {'request': request, 'user': user,
            'publications': publications})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Activate(View):
    def get(self, request, pk):
        user = models.User.objects.get(pk=pk)
        user.is_active = True
        user.save()

        messages.success(request, "{}'s account has been activated".format(user.get_full_name()), extra_tags='users')
        return redirect('website:users')

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class DeleteSub(View):
    def get(self, request, pk):
        sub = models.Subscription.objects.get(pk=pk)
        sub.delete()

        messages.success(request, "Subscription has been deleted", extra_tags='subscriptions')
        return redirect('website:subscriptions')

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class DeleteContent(View):
    def get(self, request, pk):
        pub = models.Publication.objects.get(pk=pk)
        pub.delete()

        messages.success(request, "Publication has been deleted", extra_tags='subscriptions')
        return redirect('website:content')

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class DeleteEbook(View):
    def get(self, request, pk):
        pub = models.Publication.objects.get(pk=pk)
        pub.delete()

        messages.success(request, "eBook has been deleted", extra_tags='subscriptions')
        return redirect('website:your-ebooks')

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class DeleteArticle(View):
    def get(self, request, pk):
        pub = models.Publication.objects.get(pk=pk)
        pub.delete()

        messages.success(request, "Article has been deleted", extra_tags='subscriptions')
        return redirect('website:your-articles')

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Deactivate(View):
    def get(self, request, pk):
        user = models.User.objects.get(pk=pk)
        user.is_active = False
        user.save()
        messages.success(request, "{}'s account has been deactivated".format(user.get_full_name()), extra_tags='users')
        return redirect('website:users')
'''END PORTAL VIEWS'''

'''BEGIN PUBLICATION VIEWS'''

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Step1(View):
    def get(self, request, pk):
        publication = models.Publication.objects.get(pk=pk)
        if publication.is_article():
            form = forms.ArticleForm(instance=publication)
        else:
            form = forms.eBookForm(instance=publication)

        tags = publication.tags.split(', ')
        other_tags = []
        for publication in models.Publication.objects.all():
            other_tags += publication.tags.split()
        return render(request, 'website/publication/step-1.html',
            {'request': request, 'user': request.user, 'form': form,
            'publication': publication, 'tags': tags, 'other_tags': other_tags})

    def post(self, request, pk):
        publication = models.Publication.objects.get(pk=pk)
        if publication.is_article():
            form = forms.ArticleForm(request.POST, instance=publication)
        else:
            form = forms.eBookForm(request.POST, request.FILES, instance=publication)
            
        if form.is_valid():
            form = form.save(commit=False)
            form.tags = ", ".join(map(str, request.POST.getlist('tags', [])))
            form.save()
            return redirect('website:step-2', publication.pk)
        return redirect('website:step-1', publication.pk)

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Step2(View):
    def get(self, request, pk):
        publication = models.Publication.objects.get(pk=pk)
        form = forms.ImageForm(instance=publication)
        print(publication.get_ebook())
        return render(request, 'website/publication/step-2.html',
            {'request': request, 'user': request.user, 'form': form,
            'publication': publication})

    def post(self, request, pk):
        publication = models.Publication.objects.get(pk=pk)
        form = forms.ImageForm(request.POST, request.FILES, instance=publication)
        print(request.POST)
        try:
            if form.is_valid():
                form.save()
                return redirect('website:step-3', publication.pk)
            return redirect('website:step-2', publication.pk)
        except Exception as e:
            print(e)
            return redirect('website:step-3', publication.pk)

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Step3(View):
    def get(self, request, pk):
        publication = models.Publication.objects.get(pk=pk)

        user = request.user

        if user.is_free():
            myData = {
                'merchant_id':'17547784',
                'merchant_key': 'f94fol0ztgcrc',
                'email_address': user.email,
                'amount': "79",
                'item_name': 'Tale Pro Plan Subscription',
                'subscription_type': '1',
                'recurring_amount': "79",
                'frequency': '3',
                'cycles': '0',
                
            }

            myData["signature"] = generateSignature(myData, passPhrase)
            pfParamString = dataToString(myData, passPhrase);
            identifier = generatePaymentIdentifier(pfParamString);
        else:
            identifier = ''


        return render(request, 'website/publication/step-3.html',
            {'request': request, 'user': request.user,
            'publication': publication, 'identifier': identifier})

    def post(self, request, pk):
        publication = models.Publication.objects.get(pk=pk)
        pricing = request.POST.get('publication_pricing', '0')

        publication.is_paygated = bool(int(pricing))
        if not publication.is_article():
            publication.is_published = True
        publication.save()
        if publication.is_paygated:
            if publication.is_article():
                publication.user.amount = request.POST.get('amount', 0)
                publication.user.save()
            else:
                publication.amount = request.POST.get('amount', 0)

                publication.save()

        return JsonResponse({'200': 'success', 'pk': publication.pk})

@method_decorator([login_required(login_url='website:login')], name='dispatch')
class Preview(View):
    def get(self, request, pk):
        publication = models.Publication.objects.get(pk=pk)
        tags = publication.tags.split(', ')
        tags = list(filter(None, tags))
        return render(request, 'website/publication/preview.html',
            {'request': request, 'user': request.user,
            'article': publication, 'tags': tags})
'''END PUBLICATION VIEWS'''

'''BEGIN PAYFAST VIEWS'''
class PaymentSuccess(View):
    def get(self, request, pk):
        order = models.Order.objects.get(pk=pk)
        order.status = "Paid"
        order.save()

        return redirect('website:your-orders')

class PaymentCancel(View):
    def get(self, request, pk):
        order = models.Order.objects.get(pk=pk)

        return redirect('website:your-orders')

class PaymentNotify(View):
    def post(self, request, author, subscriber):
        author = models.User.objects.get(pk=author)
        subscriber = models.User.objects.get(pk=subscriber)
        subscription = models.Subscription(author=author,
            subscriber=subscriber, amount=author.amount)

        subscription.save()

        return redirect('website:author-select', author.pk, author.username)

class ProUpgrade(View):
    def post(self, request, pk):
        publication = models.Publication.objects.get(pk=pk)
        publication.user.account_type = 2
        publication.user.save()

        if publication.is_article():
            return redirect('website:preview', publication.pk)
        else:
            return redirect('website:landing')

'''END PAYFAST VIEWS'''

class Search(View):
    def get(self, request, word):
        publications = models.Publication.objects.annotate(search=SearchVector('title', 'blurb', 'body', 'user__first_name', 'user__last_name'),).filter(search=word).filter(is_published=True).order_by('-date')
        paginator = Paginator(publications, 7)
        page = request.GET.get('page')
        publications = paginator.get_page(page)

        tags = []
        for tag in models.Publication.objects.values_list('tags', flat=True):
            tags += tag.split(', ')

        tags = list(filter(None, tags))

        authors = []

        for publication in publications:
            authors.append(publication.user)

        latest_publications = publications[:3]

        return render(request, 'website/search.html',
        {'request': request, 'publications': publications,
        'range': range(publications.paginator.num_pages), 'tags': set(tags),
        'authors': authors, 'latest_publications': latest_publications, 'word': word})

def searchPublication(request):
    if request.method == "POST":
        word = request.POST.get('search')

        return redirect('website:search', word)