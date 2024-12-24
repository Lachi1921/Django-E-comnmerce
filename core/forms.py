from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField
from .models import *


class CustomAuthenticationForm(forms.Form):
    email_or_username = forms.CharField(
        label='Email or Username',
        widget=forms.TextInput(attrs={'class': 'u-full-width bg-light pb-2', 'placeholder': 'Enter your email or username'}),
        required=True,
    )
    password = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'u-full-width bg-light pb-2', 'placeholder': 'Enter your password'}),
        required=True,
    )


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(label="Email", max_length=225, required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            field = self.fields[field_name]
            field.widget.attrs.update({'class': 'u-full-width bg-light pb-2', 'placeholder': field.label})
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email is already taken.')
        return email


class ProductCreationForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'price', 'description', 'additional_information', 'color', 'sizes', 'category', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'u-full-width bg-light pb-2', 'placeholder': 'Product Title'}),
            'price': forms.NumberInput(attrs={'class': 'u-full-width bg-light pb-2', 'placeholder': 'Product Price'}),
            'description': forms.Textarea(attrs={'class': 'u-full-width bg-light pb-2', 'placeholder': 'Product Description'}),
            'additional_information': forms.Textarea(attrs={'class': 'u-full-width bg-light pb-2', 'placeholder': 'Additional Information'}),
            'color': forms.SelectMultiple(attrs={'class': 'u-full-width bg-light pb-2', 'placeholder': 'Product Color'}),
            'sizes': forms.SelectMultiple(attrs={'class': 'u-full-width bg-light pb-2', 'placeholder': 'Select Sizes'}),
            'category': forms.Select(attrs={'class': 'u-full-width bg-light pb-2', 'placeholder': 'Select Category'}),
            'tags': forms.TextInput(attrs={'class': 'u-full-width bg-light pb-2', 'data-role': 'tagsinput'}),
        }

    def clean_tags(self):
        tags = self.cleaned_data['tags']
        if len(tags) > 5:
            raise ValidationError("You can only input up to 5 tags.")
        return tags

class ImageCreationForm(forms.ModelForm):
    images = forms.ImageField(required=True, widget=forms.ClearableFileInput())

    class Meta:
        model = Image
        fields = ['images']

    def clean_images(self):
        images = self.cleaned_data['images']
        if not images:
            raise ValidationError("This field is required.")
        if len(images) > 3:
            raise ValidationError("You can only input up to 3 images.")
        for image in images:
            if image.size > 5 * 1024 * 1024:
                raise ValidationError(f"{image} exceeds the 5MB file size limit.")
        return images

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['content', 'rating']

    content = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'cols': 40, 'class': 'u-full-width', 'placeholder': 'Write your review here'}),
        max_length=200,
        required=True,
    )
    
    rating = forms.IntegerField(
        validators=[
            MaxValueValidator(5, message="Rating cannot be greater than 5."),
            MinValueValidator(1, message="Rating cannot be less than 1.")
        ],
        widget=forms.NumberInput(attrs={'class': 'u-full-width', 'placeholder': 'Write your rating here'}),
        required=True,
    )

class CartItemForm(forms.ModelForm):
    quantity = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'u-full-width'}), required=True)

    class Meta:
        model = CartItem
        fields = ['quantity', 'color', 'size']

    def __init__(self, *args, **kwargs):
        product = kwargs.pop('product', None)
        super().__init__(*args, **kwargs)
        if product and product.is_clothing:
            self.fields['size'] = forms.ModelChoiceField(
                queryset=Size.objects.filter(product=product),
                required=True,
                widget=forms.Select(attrs={'class': 'form-select form-control u-full-width'})
            )
        else:
            del self.fields['size']

        self.fields['color'] = forms.ModelChoiceField(
            queryset=Color.objects.filter(product=product),
            required=True,
            widget=forms.Select(attrs={'class': 'form-select form-control'})
        )

# class UpdateCartItemForm(forms.Form):
#     quantity = forms.IntegerField(
#         widget=forms.NumberInput(attrs={'class': 'spin-number-output'}),
#         min_value=1,
#         max_value=100,
#     )

class SearchForm(forms.Form):
    q = forms.CharField(
        label='',
        widget=forms.TextInput(
            attrs={
                'id': 'search-form',
                'class': 'search-field',
                'placeholder': 'Type and press enter',
                'name': 'q',
                'type': 'search'
            }
        )
    )

class CheckoutForm(forms.Form):
    street_address = forms.CharField(max_length=255, required=False)
    apartment_address = forms.CharField(max_length=255, required=False)
    zip_code = forms.CharField(max_length=10, required=False)
    country = forms.ChoiceField(choices=CountryField().choices, required=False)
    use_default_billing_address = forms.BooleanField(label="Use Default Billing Address?", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input flex-shrink-0'}))
    save_this_as_default_billing_address = forms.BooleanField(label="Save it as default billing address?", required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input flex-shrink-0'}))
    
    PAYMENT_CHOICES = (
        ('CreditCard', 'Credit Card'),
        ('PayPal', 'PayPal'),
    )
    payment_method = forms.ChoiceField(choices=PAYMENT_CHOICES, widget=forms.RadioSelect(attrs={'class':'form-check-input flex-shrink-0'}), required=True)
    order_notes = forms.CharField(label="Order notes", widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Notes about your order. Like special notes for delivery.'}), required=False)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.fields:
            field = self.fields[field_name]
            field.widget.attrs.update({'class': 'form-control'})

