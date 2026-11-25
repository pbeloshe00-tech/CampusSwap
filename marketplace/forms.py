
from django import forms
from django.contrib.auth.models import User
from .models import Product, ExchangeRequest, SellerReview


class ProductForm(forms.ModelForm):

    class Meta:
        model = Product

        fields = [
            'name',
            'category',
            'description',
            'price',
            'image'
        ]

        widgets = {
            'description': forms.Textarea(
                attrs={'rows': 4}
            ),
        }


class ProfileForm(forms.ModelForm):

    class Meta:
        model = User

        fields = [
            'username',
            'first_name',
            'last_name',
            'email'
        ]

        widgets = {
            'username': forms.TextInput(
                attrs={'placeholder': 'Enter username'}
            ),
            'first_name': forms.TextInput(
                attrs={'placeholder': 'Enter first name'}
            ),
            'last_name': forms.TextInput(
                attrs={'placeholder': 'Enter last name'}
            ),
            'email': forms.EmailInput(
                attrs={'placeholder': 'Enter email address'}
            ),
        }


# EXCHANGE REQUEST FORM
class ExchangeRequestForm(forms.ModelForm):

    class Meta:
        model = ExchangeRequest

        fields = ['message']

        widgets = {
            'message': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Why are you interested in exchanging this product?'
                }
            ),
        }

        labels = {
            'message': 'Message to Seller'
        }


# SELLER REVIEW FORM
class SellerReviewForm(forms.ModelForm):

    class Meta:
        model = SellerReview

        fields = [
            'rating',
            'comment'
        ]

        widgets = {
            'rating': forms.Select(
                choices=[
                    (5, '⭐⭐⭐⭐⭐ Excellent'),
                    (4, '⭐⭐⭐⭐ Very Good'),
                    (3, '⭐⭐⭐ Good'),
                    (2, '⭐⭐ Fair'),
                    (1, '⭐ Poor'),
                ]
            ),

            'comment': forms.Textarea(
                attrs={
                    'rows': 4,
                    'maxlength': 500,
                    'placeholder': 'Share your experience with this seller...'
                }
            ),
        }

        labels = {
            'rating': 'Rate the Seller',
            'comment': 'Write Your Review'
        }
