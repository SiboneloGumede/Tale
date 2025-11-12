from django import forms
from django.contrib.auth import (
    authenticate, get_user_model, password_validation,
)
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.forms import (UsernameField, 
    UserModel, UserCreationForm, AuthenticationForm)
from django.utils.text import capfirst
from django.core.exceptions import ValidationError
from website.models import User
from website import models
from PIL import Image


class LoginForm(AuthenticationForm):
    """
    Base class for authenticating users. Extend this to get a form that accepts
    username/password logins.
    """
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus': True, 
    	'class': 'form-control form-control-lg', 'placeholder': 'Email address'}))
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password',
        	'class': 'form-control form-control-lg', 'placeholder': '********'}),
    )

    error_messages = {
        'invalid_login': _(
            "Please enter a correct %(username)s and password. Note that both "
            "fields may be case-sensitive."
        ),
        'inactive': _("This account is inactive."),
    }

    

class SetPasswordForm(forms.Form):
    """
    A form that lets a user change set their password without entering the old
    password
    """
    error_messages = {
        'password_mismatch': _('The two password fields didn’t match.'),
    }
    new_password1 = forms.CharField(
        label=_("New password"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
        help_text=password_validation.password_validators_help_text_html(),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_new_password2(self):
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2:
            if password1 != password2:
                raise ValidationError(
                    self.error_messages['password_mismatch'],
                    code='password_mismatch',
                )
        password_validation.validate_password(password2, self.user)
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user

class Step1Form(forms.ModelForm):
    class Meta:
        model = models.Publication

        fields = ['publication_type',]

        widgets = {
        'publication_type':forms.Select(attrs={'class': 'js-select form-select', }),
        }

class ArticleForm(forms.ModelForm):
    class Meta:
        model = models.Publication

        fields = ['title', 'blurb', 'body']

        widgets = {
        'title':forms.TextInput(attrs={'class': 'form-control', 'required': 'required', 'placeholder': 'Title of your publication'}),
        }

class eBookForm(forms.ModelForm):
    class Meta:
        model = models.Publication

        fields = ['title', 'blurb', 'upload',]

        widgets = {
        'title':forms.TextInput(attrs={'class': 'form-control', 'required': 'required', 'placeholder': 'Title of your publication'}),
        }

class Step4Form(forms.ModelForm):
    class Meta:
        model = models.Publication

        fields = ['is_paygated',]

        widgets = {
        'publication_type':forms.Select(attrs={'class': 'js-select form-select', }),
        }

class ImageForm(forms.ModelForm):
    x = forms.FloatField(widget=forms.HiddenInput())
    y = forms.FloatField(widget=forms.HiddenInput())
    width = forms.FloatField(widget=forms.HiddenInput())
    height = forms.FloatField(widget=forms.HiddenInput())

    class Meta:
        model = models.Publication
        fields = ('image', 'x', 'y', 'width', 'height', )

    def save(self):
        photo = super(ImageForm, self).save()

        x = self.cleaned_data.get('x')
        y = self.cleaned_data.get('y')
        w = self.cleaned_data.get('width')
        h = self.cleaned_data.get('height')

        image = Image.open(photo.image)
        cropped_image = image.crop((x, y, w+x, h+y))
        resized_image = cropped_image.resize((600, 600), Image.ANTIALIAS)
        resized_image.save(photo.image.path)

        return photo

class ProfilePhotoForm(forms.ModelForm):
    x = forms.FloatField(widget=forms.HiddenInput())
    y = forms.FloatField(widget=forms.HiddenInput())
    width = forms.FloatField(widget=forms.HiddenInput())
    height = forms.FloatField(widget=forms.HiddenInput())

    class Meta:
        model = models.User
        fields = ('image', 'x', 'y', 'width', 'height', )

    def save(self):
        photo = super(ProfilePhotoForm, self).save()

        x = self.cleaned_data.get('x')
        y = self.cleaned_data.get('y')
        w = self.cleaned_data.get('width')
        h = self.cleaned_data.get('height')

        image = Image.open(photo.image)
        cropped_image = image.crop((x, y, w+x, h+y))
        resized_image = cropped_image.resize((160, 160), Image.ANTIALIAS)
        resized_image.save(photo.image.path)

        return photo

class UserForm(forms.ModelForm):
    class Meta:
        model = models.User
        fields = ('username', 'first_name', 'last_name', 'phone')
        widgets = {
            'username':forms.EmailInput(attrs={'required': 'required','class':'form-control form-control-lg','placeholder':'Email'}),
            'first_name':forms.TextInput(attrs={'required':'required','class':'form-control form-control-lg','placeholder':'First name'}),
            'last_name':forms.TextInput(attrs={'required':'required','class':'form-control form-control-lg','placeholder':'Last name'}),
            'phone':forms.TextInput(attrs={'required':'required','class':'form-control form-control-lg','placeholder':'Phone number'}),
            }

class SignUpForm(UserCreationForm):

    class Meta:
        model = models.User
        fields = ('username', 'email', 'password1', 'password2', )
        