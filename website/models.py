from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from ckeditor_uploader.fields import RichTextUploadingField
from ckeditor.fields import RichTextField
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.urls import reverse
from optimized_image.fields import OptimizedImageField
from website.api.views import f
from website.payfast import create_payment
import hashlib
import urllib.parse

# Create your models here.

def user_directory_path(instance, filename):
	return 'uploads/user_{0}/{1}/{2}'.format(instance.user.folder_name(), instance.title, filename)

def profile_photo_path(instance, filename):
	return 'profile_photos/{0}/{1}'.format(instance.folder_name(), filename)

class User(AbstractUser):
	USER_TYPE_CHOICES = (
		(1, 'admin'),
		(2, 'user'),
	)
	ACCOUNT_TYPE_CHOICES = (
		(1, 'FREE'),
		(2, 'PRO'),
	)

	GENDER_CHOICES = (
		(1, 'MALE'),
		(2, 'FEMALE'),
		(3, 'OTHER')
	)
	user_type = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=1)
	account_type = models.PositiveSmallIntegerField(choices=ACCOUNT_TYPE_CHOICES, default=1)
	gender = models.PositiveSmallIntegerField(choices=GENDER_CHOICES, default=1)
	image = OptimizedImageField(upload_to='', default='tale-logo.svg')
	bio = models.TextField(blank=True)
	phone = models.CharField(max_length=36)
	merchant_id = models.IntegerField(default=0)
	amount = models.DecimalField(max_digits=8, decimal_places=2, default=5.00)
	expiry_date = models.DateTimeField(default=timezone.now)

	address_line_1 = models.CharField(max_length=256)
	address_line_2 = models.CharField(max_length=256, blank=True)
	city = models.CharField(max_length=256)
	province = models.CharField(max_length=256)
	postal_code = models.CharField(max_length=256)
	country = models.CharField(max_length=256)

	has_notifications = models.BooleanField(default=True)

	def has_paid(self):
		if self.expiry_date > timezone.now():
			return True
		else:
			return False

	def is_zero(self):
		if self.merchant_id == 0:
			return True
		else:
			return False

	def initials(self):
		return "{}{}".format(self.first_name[0], self.last_name[0])

	def is_admin(self):
		if self.user_type == 1:
			return True
		else:
			return False

	def is_user(self):
		if self.user_type == 2:
			return True
		else:
			return False

	def is_free(self):
		if self.account_type == 1:
			return True
		else:
			return False

	def is_pro(self):
		if self.account_type == 2:
			return True
		else:
			return False

	def account_type_text(self):
		if self.account_type == 1:
			return "Free"
		else:
			return "Paid"

	def is_male(self):
		if self.gender == 1:
			return True
		else:
			return False

	def is_female(self):
		if self.gender == 2:
			return True
		else:
			return False

	def is_other(self):
		if self.gender == 3:
			return True
		else:
			return False

	def folder_name(self):
		return self.get_full_name().lower().replace(' ', '_')

	def publications(self):
		return self.publication_set.filter(is_published=True).order_by('-date')

	def publications_count(self):
		return self.publications().count()

	def subscriptions_count(self):
		return Subscription.objects.filter(author=self).filter(is_active=True).count()

	def publications_percentage(self):
		return self.publications().count()/10*100

	def gravatar(self):
		try:
			return self.image.url
		except Exception:
			return ''

	def billing_address(self):
		if self.address_line_2:
			return "{}, {}, {}, {}, {}, {}".format(self.address_line_1,
				self.address_line_2,
				self.city, self.province, self.country, self.postal_code)
		else:
			return "{}, {}, {}, {}, {}".format(self.address_line_1,
				self.city, self.province, self.country, self.postal_code)

class Contact(models.Model):
	date = models.DateTimeField(default=timezone.now)
	name = models.CharField(max_length=36)
	email = models.EmailField()
	phone = models.CharField(max_length=36)
	message = models.TextField()

	def __str__(self):
		return self.name

class Subscribe(models.Model):
	date = models.DateTimeField(default=timezone.now)
	email = models.EmailField()

	def __str__(self):
		return self.email

from django.conf import settings
from django.db import models
from ckeditor_uploader.fields import RichTextUploadingField
from imagekit.models import ProcessedImageField  # or OptimizedImageField if using that

def user_directory_path(instance, filename):
    # keep your existing logic
    return f'user_{instance.user.id}/{filename}'

class Publication(models.Model):
    PUBLICATION_TYPE_CHOICES = (
        ('eBook', 'eBook'),
        ('Article', 'Article'),
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateTimeField(default=timezone.now)
    publication_type = models.CharField(max_length=36, choices=PUBLICATION_TYPE_CHOICES)
    title = models.CharField(max_length=1024)
    blurb = models.TextField()
    body = RichTextUploadingField(blank=True)
    tags = models.TextField()
    upload = models.FileField(upload_to=user_directory_path, blank=True)
    amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    is_paygated = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)

    # Set default placeholder image
    image = OptimizedImageField(
        upload_to=user_directory_path,
        blank=True,
        null=True,
        default='assets/img/tale/tale-logo.png')  

    def get_image(self):
        if self.image:
            return self.image.url
        # fallback in case default fails
        return settings.STATIC_URL + 'assets/img/tale/tale-logo.png'

    def is_article(self):
        return self.publication_type == "Article"

    def slug(self):
        return self.title.lower().replace(' ', '-')

    def amount_locale(self):
        return "{:,.2f}".format(self.amount)

    def get_ebook(self):
        try:
            return self.upload.url
        except Exception as e:
            print(e)
            return ''

    def __str__(self):
        return self.title

class OrderDetail(models.Model):
	content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
	object_id = models.PositiveIntegerField()
	content_object = GenericForeignKey()
	publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
	quantity = models.PositiveSmallIntegerField(default=0)

	def __str__(self):
		return self.publication.title

	class Meta:
		verbose_name_plural = "Order Details"


class Order(models.Model):
	STATUS_CHOICES = [('Awaiting Payment', 'Awaiting Payment'),
	('Paid', 'Paid'),]

	user = models.ForeignKey(User, on_delete=models.CASCADE)
	placed = models.DateTimeField(default=timezone.now)
	status = models.CharField(max_length=256, choices=STATUS_CHOICES, default="Awaiting Payment")

	order_details =  GenericRelation(OrderDetail, related_name='order_details', related_query_name='order')

	def order_number(self):
		return self.user.initials() + "{:02d}".format(self.pk)

	def status_label(self):
		if self.status == "Awaiting Payment":
			return "danger"
		else:
			return "success"

	def len_order(self):
		return self.order_details.all().count()

	def small_order(self):
		if self.len_order() == 1:
			return True
		else:
			return False

	def total_value_nonlocale(self):
		total = 0

		for order_detail in self.order_details.all():
			total += order_detail.amount

		return total

	def is_free(self):
		if self.total_value_nonlocale() == 0:
			return True
		else:
			return False

	def total_value(self):
		total = 0

		for order_detail in self.order_details.all():
			total += order_detail.amount

		return "{:,.2f}".format(total)

	def payment_link(self):
		success = urllib.parse.quote("https://www.taleapp.io" + reverse('website:your-orders'))
		cancel = urllib.parse.quote("https://www.taleapp.io" + reverse('website:your-orders'))
		notify = urllib.parse.quote("https://www.taleapp.io" + reverse('api:callback', kwargs={'order': f.encrypt(str(self.pk).encode('utf-8'))}))
		return create_payment(self.total_value_nonlocale(),
			"Tale: {}".format(self.user.get_full_name()), success,
			cancel, notify)

	def __str__(self):
		return self.user.username


class Cart(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	order_details =  GenericRelation(OrderDetail, related_name='order_details')

	def is_empty(self):
		count = self.order_details.all().count()
		if count > 0:
			return False
		else:
			return True

	def total_value_nonlocale(self):
		total = 0

		for order_detail in self.order_details.all():
			total += order_detail.amount

		return total

	def is_free(self):
		if self.total_value_nonlocale() == 0:
			return True
		else:
			return False

	def total_value(self):
		total = 0

		for order_detail in self.order_details.all():
			total += order_detail.amount

		return "{:,.2f}".format(total)

	def __str__(self):
		return self.user.username


class AnonymousCart(models.Model):
	user = models.CharField(max_length=128, unique=True)
	order_details =  GenericRelation(OrderDetail, related_name='order_details')

	def is_empty(self):
		count = self.order_details.all().count()
		if count > 0:
			return False
		else:
			return True

	def total_value_nonlocale(self):
		total = 0

		for order_detail in self.order_details.all():
			total += order_detail.amount

		return total

	def total_value(self):
		total = 0

		for order_detail in self.order_details.all():
			total += order_detail.amount

		return "{:,.2f}".format(total)


	def __str__(self):
		return self.user

@receiver(post_save, sender=User)
def create_cart_object(sender, instance, created, **kwargs):
	if created:
		cart = Cart.objects.create(user=instance)

class Subscription(models.Model):
	date = models.DateTimeField(default=timezone.now)
	author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author')
	subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriber')
	amount = models.DecimalField(max_digits=8, decimal_places=2)
	token = models.CharField(max_length=64)
	is_active = models.BooleanField(default=False)
	quantity = models.PositiveSmallIntegerField(default=1)

	def amount_locale(self):
		return "{:,.2f}".format(self.amount)

	def status(self):
		if self.is_active:
			return '<span class="badge bg-success">Active</span>'
		else:
			return '<span class="badge bg-danger">Inactive</span>'

	def __str__(self):
		return "%s is subscribed to %s" % (self.subscriber.get_full_name(), 
			self.author.get_full_name())

class ArticleRead(models.Model):
	date = models.DateTimeField(default=timezone.now)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	publication = models.ForeignKey(Publication, on_delete=models.CASCADE)
	quantity = models.PositiveSmallIntegerField(default=1)

	def __str__(self):
		return "%s has read %s" % (self.user.get_full_name(), self.publication.title)
	
class SubscriptionPayment(models.Model):
	date = models.DateTimeField(default=timezone.now)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=8, decimal_places=2)

	def amount_locale(self):
		return "{:,.2f}".format(self.amount)

class SavedQuickRead(models.Model):
	date = models.DateTimeField(default=timezone.now)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	publication = models.ForeignKey(Publication, on_delete=models.CASCADE)

	def __str__(self):
		return "%s has saved %s" % (self.user.get_full_name(), self.publication.title)

class TalePayment(models.Model):
	date = models.DateTimeField(default=timezone.now)
	user = models.ForeignKey(User, on_delete=models.CASCADE)
	amount = models.DecimalField(max_digits=8, decimal_places=2)

	def amount_locale(self):
		return "{:,.2f}".format(self.amount)
