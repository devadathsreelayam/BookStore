from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Reader, Genre


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'form-control',
        'placeholder': 'your.email@example.com'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'First Name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'form-control',
        'placeholder': 'Last Name'
    }))
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={
        'class': 'form-control',
        'type': 'date'
    }))
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={
        'class': 'form-control',
        'rows': 3,
        'placeholder': 'Tell us about your reading preferences...'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['date_of_birth', 'bio']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})


class ReaderInterestsForm(forms.ModelForm):
    interests = forms.ModelMultipleChoiceField(
        queryset=Genre.objects.filter(parent__isnull=True),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Select your favorite genres (choose 3-4)"
    )

    class Meta:
        model = Reader
        fields = ['interests', 'bio', 'date_of_birth']


class CustomAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})
