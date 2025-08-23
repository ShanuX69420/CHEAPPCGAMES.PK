from django import forms


class CheckoutForm(forms.Form):
    email = forms.EmailField()
    name = forms.CharField(max_length=200, required=False)

