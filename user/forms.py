from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from user.models import Contact

class ContactForm(forms.ModelForm):
    class Meta:
        model = Contact
        fields = ['firstname', 'lastname', 'phone', 'email', 'message']

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username','first_name', 'last_name', 'email', 'password1', 'password2']


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']  # Exclude password fields

    def __init__(self, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        # Add individual styles to fields
        self.fields['username'].widget.attrs.update({'class': 'form-input px-4 py-2 rounded-lg w-full', 'placeholder': 'Enter Username'})
        self.fields['first_name'].widget.attrs.update({'class': 'form-input px-4 py-2 rounded-lg w-full', 'placeholder': 'First Name'})
        self.fields['last_name'].widget.attrs.update({'class': 'form-input px-4 py-2 rounded-lg w-full', 'placeholder': 'Last Name'})
        self.fields['email'].widget.attrs.update({'class': 'form-input px-4 py-2 rounded-lg w-full', 'placeholder': 'Email'})


        