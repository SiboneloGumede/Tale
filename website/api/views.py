from website import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from cryptography.fernet import Fernet
from website.functions import add_months
from datetime import timedelta
from django.template.loader import render_to_string

key ='tgh_xGv6qjpP3HTAo-ewNAl5uwUhVBEa_COk-oqeuHw='
f = Fernet(key)

class WebhookView(APIView):

	def post(self, request, user, author, format=None):	
		send_mail('payfast tale', '{}'.format(request.data), 'no-reply@airos.co.za',
			['brandonc@airos.co.za'])

		data = request.data
		user = get_object_or_404(models.User, pk=int(f.decrypt(user))) 
		author = get_object_or_404(models.User, pk=int(f.decrypt(author))) 

		if data['payment_status'] == "COMPLETE":
			is_subscribed = models.Subscription.objects.filter(subscriber=user).filter(author=author).filter(is_active=True).exists()
			if is_subscribed:
				subscription = models.Subscription.objects.filter(subscriber=user).filter(author=author).filter(is_active=True).first()
			else:
				subscription = models.Subscription(subscriber=user, author=author, amount=data['amount_gross'],
					is_active=True, token=data['token'])
				subscription.save()
				
				if author.has_notifications:
					new_sub = render_to_string('website/email/new-subscriber.html', {'name': author.first_name})

					send_mail(
					    subject='[Tale] {}, you have 1 new subscriber'.format(author.first_name),
					    message='',
					    from_email='no-reply@taleapp.io',
					    recipient_list=[
					    author.email,
					    ],
					    html_message=new_sub,
					)

			payment = models.SubscriptionPayment(user=user, subscription=subscription,
				amount=data['amount_gross'])
			payment.save()
			
			return Response({'Success': 'Payment has been COMPLETED'}, status=200)
		else:
			return Response({'Forbidden': 'Payment has not been successful'}, status=403)

class CallbackView(APIView):

	def post(self, request, order, format=None):	
		send_mail('payfast tale callback', '{}'.format(request.data), 'no-reply@airos.co.za',
			['brandonc@airos.co.za'])

		data = request.data
		order = get_object_or_404(models.Order, pk=int(f.decrypt(order))) 

		if data['payment_status'] == "COMPLETE":
			order.status = "Paid"
			order.save()
			
			return Response({'Success': 'Payment has been COMPLETED'}, status=200)
		else:
			return Response({'Forbidden': 'Payment has not been successful'}, status=403)

class PaymentView(APIView):

	def post(self, request, user, format=None):	
		send_mail('payfast tale', '{}'.format(request.data), 'no-reply@airos.co.za',
			['brandonc@airos.co.za'])

		data = request.data
		user = get_object_or_404(models.User, pk=int(f.decrypt(user))) 

		if data['payment_status'] == "COMPLETE":

			payment = models.TalePayment(user=user,
				amount=data['amount_gross'])
			payment.save()
			user.account_type = 2
			if payment.amount > 80:
				user.expiry_date = user.expiry_date + timedelta(days=366)
			else:
				user.expiry_date = add_months(user.expiry_date, 1)
			user.save()
			
			return Response({'Success': 'Payment has been COMPLETED'}, status=200)
		else:
			return Response({'Forbidden': 'Payment has not been successful'}, status=403)