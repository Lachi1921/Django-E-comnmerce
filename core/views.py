from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView)
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from .forms import *
from .models import *
from django.db.models import Q
from django.urls import reverse
from taggit.models import Tag
from django.db.models import Count
from django.db.models.functions import Coalesce
from django.contrib.auth.decorators import login_required
import stripe
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import logging
from django.core.mail import send_mail



stripe.api_key = settings.STRIPE_SECRET_KEY
def home(request):
    slides = Slideshow.objects.all()
    reviews = Review.objects.all()
    products = Product.objects.all()
    categories = Category.objects.all()
    searchform = SearchForm(request.GET)
    context = {
        'slides': slides,
        'reviews': reviews,
        'products': products,
        'categories': categories,
        'searchform': searchform,
    }
    return render(request, 'index.html', context)

def search_view(request):
    query = None
    results = None

    if request.method == 'GET':
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['q']
            results = Product.objects.filter(title__icontains=query)

    return render(request, 'search_results.html', {'results': results, 'query': query})

def login_register_view(request):
    login_form = CustomAuthenticationForm()
    registration_form = CustomUserCreationForm()

    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':

        if 'login' in request.POST:
            login_form = CustomAuthenticationForm(request.POST)
            if login_form.is_valid():
                email_or_username = login_form.cleaned_data['email_or_username']
                password = login_form.cleaned_data['password']
                users = User.objects.filter(Q(username=email_or_username) | Q(email=email_or_username))
                if users.exists():
                    user = authenticate(request, username=users[0].username, password=password)
                    if user is not None:
                        login(request, user)
                        return redirect('core:home')
                    else:
                        error_message = 'Invalid username or password.'
                        context = {
                            'login_form': login_form,
                            'registration_form': registration_form,
                            'error_message': error_message,
                        }
                        return render(request, 'accounts/login_register.html', context)

            else:
                return render(request, 'accounts/login_register.html', {
                    'login_form': login_form,
                    'registration_form': registration_form
                })

        elif 'register' in request.POST:
            registration_form = CustomUserCreationForm(request.POST)
            if registration_form.is_valid():
                user = User.objects.create_user(
                    username=registration_form.cleaned_data['username'],
                    email=registration_form.cleaned_data['email'],
                    password=registration_form.cleaned_data['password1']
                )
                user.save()
                login(request, user)
                return redirect('core:home')

            else:
                return render(request, 'accounts/login_register.html', {
                    'login_form': login_form,
                    'registration_form': registration_form
                })

    context = {
        'login_form': login_form,
        'registration_form': registration_form,
    }

    return render(request, 'accounts/login_register.html', context)


class CustomPasswordResetView(PasswordResetView):
    template_name = 'accounts/password_reset_form.html'
    email_template_name = 'accounts/password_reset_email.html'
    success_url = reverse_lazy('core:password_reset_done')

    def form_valid(self, form):
        self.request.session['is_initiated'] = True
        return super().form_valid(form)

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('is_initiated', False):
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'accounts/password_reset_confirm.html'
    success_url = reverse_lazy('core:password_reset_complete')

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('is_initiated', False):
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.session.get('is_initiated', False):
            return redirect('core:home')
        return super().dispatch(request, *args, **kwargs)

def logout_view(request):
    if not request.user.is_authenticated:
        return redirect(reverse('core:home'))
    logout(request)
    return redirect(reverse('core:login_register'))

@login_required(login_url='core:login_register')
def create_product(request):
    p_form = ProductCreationForm(request.POST or None)
    i_form = ImageCreationForm(request.FILES or None)
    errors = []
    if request.method == 'POST':
        images = request.FILES.getlist('images')
        if p_form.is_valid():
            if images:
                if len(images) <= 3:
                    product = p_form.save(commit=False)
                    product.user = request.user.userprofile
                    product.save()
                    p_form.save_m2m()

                    for product_image in images[:3]:
                        Image.objects.create(product=product, images=product_image)

                    return redirect('core:product-details', product_slug=product.slug)
                else:
                    errors.append("You can only upload up to 3 images.")
                    
            else:
                errors.append("This field is required.")

    context = {'p_form': p_form, 'i_form': i_form, 'errors': errors}
    return render(request, 'create-product.html', context)

def products(request):
    price_range = request.GET.get('price_range')
    slides = Slideshow.objects.all()
    products = Product.objects.all()
    categories = Category.objects.all()
    popular_tags = Tag.objects.annotate(num_times=Coalesce(Count('taggit_taggeditem_items'), 0)).order_by('-num_times')[:5]
    if price_range:
        min_price, max_price = map(int, price_range.split('-'))
        filtered_products = products.filter(price__gte=min_price, price__lt=max_price)

        if not filtered_products.exists():
            products = Product.objects.all()
       

    context = {
        'slides': slides,
        'products': products,
        'categories': categories,
        'popular_tags': popular_tags,
    }
    return render(request, 'shop.html', context)

def product_details(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    images = product.image_set.all()
    reviews = Review.objects.filter(product=product)
    user_already_reviewed = False
    product_owner_reviewing = False

    if request.user.is_authenticated:
        user_reviews = Review.objects.filter(product=product, user=request.user.userprofile)
        if user_reviews.exists():
            user_already_reviewed = True
    if request.user.is_authenticated and request.user.userprofile == product.user:
        product_owner_reviewing = True

    active_tab = 'description'
    cart_item_form = CartItemForm(product=product)

    if request.method == 'POST':
        review_form = ReviewForm(request.POST)
        if review_form.is_valid():
            new_review = review_form.save(commit=False)
            new_review.product = product
            new_review.user = request.user.userprofile
            new_review.rating = review_form.cleaned_data['rating']
            new_review.content = review_form.cleaned_data['content']
            new_review.save()
            active_tab = 'reviews'
            return redirect('core:product-details', product_slug=product_slug)

        else:
            print("Not valid form")
            active_tab = 'reviews'
            return render(request, 'single-product.html', {'review_form': review_form, 'active_tab': active_tab})
    else:
        review_form = ReviewForm()

    for review in reviews:
        review.star_ratings = range(review.rating)
        review.empty_star_ratings = range(5 - review.rating)

    context = {
        'product': product,
        'images': images,
        'reviews': reviews,
        'review_form': review_form,
        'active_tab': active_tab,
        'user_already_reviewed': user_already_reviewed,
        'product_owner_reviewing': product_owner_reviewing,
        'cart_item_form': cart_item_form,
    }
    return render(request, 'single-product.html', context)

@login_required(login_url='core:login_register')
def view_cart(request):
    user_profile = request.user.userprofile
    cart_items = CartItem.objects.filter(user=user_profile)
    total_price = sum(item.calculate_item_price() for item in cart_items)
    if request.method == 'POST':
        if 'update-cart' in request.POST:
            item_ids = request.POST.getlist('item_id')
            for item in item_ids:
                quantity = request.POST.get(f'quantity[{item}]', 1)
                cart_item = get_object_or_404(CartItem, id=item, user=request.user.userprofile)
                cart_item.quantity = quantity
                cart_item.save()

            return redirect('core:view-cart')
        if 'remove-cart' in request.POST:
            item_id = request.POST.get('remove-cart')
            cart_item = get_object_or_404(CartItem, id=item_id, user=request.user.userprofile)

            if cart_item.user == request.user.userprofile:
                cart_item.delete()

            return redirect('core:view-cart')
        
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }

    return render(request, 'cart.html', context)

@login_required(login_url='core:login_register')
def add_to_cart(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)

    cart_item_form = CartItemForm(request.POST or None, product=product)

    if request.method == 'POST' and cart_item_form.is_valid():
        quantity = cart_item_form.cleaned_data['quantity'] or 1
        color = cart_item_form.cleaned_data['color']
        size = cart_item_form.cleaned_data['size'] if hasattr(product, 'size') else None
        cart_item, created = CartItem.objects.get_or_create(
            user=request.user.userprofile,
            product=product,
            color=color,
        )
        if size is not None:
            cart_item.size = size

        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        else:
            cart_item.quantity = quantity

        cart_item.save()

        return redirect(reverse('core:view-cart'))

    return render(request, 'add-to-cart.html', {'product': product, 'cart_item_form': cart_item_form})

@login_required
def edit_product(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    if product.user == request.user.userprofile:
        p_form = ProductCreationForm(request.POST or None, instance=product)
        i_form = ImageCreationForm(request.POST, request.FILES, instance=product)
        errors = []
        if request.method == 'POST':
            images = request.FILES.getlist('images')
            if p_form.is_valid():
                if images:
                    if len(images) <= 3:
                        product = p_form.save(commit=False)
                        product.user = request.user.userprofile
                        product.save()
                        p_form.save_m2m()

                        for product_image in images[:3]:
                            Image.objects.create(product=product, images=product_image)

                        return redirect('core:product-details', product_slug=product.slug)
                    else:
                        errors.append("You can only upload up to 3 images.")
                        
                else:
                    errors.append("This field is required.")

        context = {'p_form': p_form, 'i_form': i_form, 'errors': errors}
        return render(request, 'edit-product.html', context)
    else:
        return redirect('core:home')

@login_required
def product_list(request):
    products = Product.objects.filter(user=request.user.userprofile)

    if 'delete_product' in request.POST:
        product_id = request.POST.get('delete_product')
        product = Product.objects.get(id=product_id, user=request.user.userprofile)
        product.delete()
        return redirect('core:product_list')

    return render(request, 'product_list.html', {'products': products})

@login_required(login_url='core:login_register')
def checkout(request, item_id):
    user_profile = request.user.userprofile
    cart = get_object_or_404(CartItem, id=item_id, user=user_profile)
    total_price = cart.calculate_item_price()
    has_existing_billing_address = Address.objects.filter(user=user_profile).exists()
    billing_address_instance = Address.objects.filter(user=user_profile, default=True).first()
    form = CheckoutForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        order, _ = Order.objects.get_or_create(user=user_profile, cart=cart)
        default_billing_address = form.cleaned_data['use_default_billing_address']

        if default_billing_address:
            billing_address = Address.objects.filter(user=user_profile, default=True).first()
            order.billing_address = billing_address
        else:
            new_billing_address = Address(
                user=user_profile,
                street_address=form.cleaned_data['street_address'],
                apartment_address=form.cleaned_data['apartment_address'],
                zip_code=form.cleaned_data['zip_code'],
                country=form.cleaned_data['country'],
                default=True
            )
            new_billing_address.save()
            order.billing_address = new_billing_address

        if form.cleaned_data['order_notes']:
            order.order_note = form.cleaned_data['order_notes']

        order.save()
        payment_method = form.cleaned_data.get('payment_method')

        if payment_method:
            return redirect('core:payment', payment_method='card', item_id=item_id)
    else:
        print(form.errors)
    context = {
        'total_price': total_price,
        'form': form,
        'has_existing_billing_address': has_existing_billing_address,
        'billing_address_instance': billing_address_instance,
    }
    return render(request, 'checkout.html', context)

@login_required(login_url='core:login_register')
def payment(request, payment_method, item_id):
    user_profile = request.user.userprofile
    cart = get_object_or_404(CartItem, id=item_id, user=user_profile)
    total_price = cart.calculate_item_price()
    billing_address_exists = Address.objects.filter(user=user_profile).exists()
    context = {'total_price': total_price, 'stripe_public_key': settings.STRIPE_PUBLISHABLE_KEY}
    print(request.user.email)

    if billing_address_exists:
        try:
            payment_session = stripe.checkout.Session.create(
                payment_method_types=[payment_method],
                line_items=[{
                    'price_data': {
                        'currency': 'usd',
                        'product_data': {
                            'name': cart.product.title,
                        },
                        'unit_amount': int(cart.product.price * 100),
                    },
                    'quantity': cart.quantity,
                }],
                customer_email=f'{request.user.email}',
                mode='payment',
                metadata={
                    'item_id': cart.id,
                    'item_name': cart.product.title,
                    'user_id': user_profile.id,
                    'userprofile': user_profile,
                    'payment_method': payment_method,
                },
                success_url=request.build_absolute_uri(reverse('core:success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('core:cancel')),
            )

            context['session_id'] = payment_session.id

        except stripe.error.StripeError as e:
            messages.error(request, str(e))

        return redirect(payment_session.url, code=303)
            
    else:
        messages.warning(request, 'Please add a billing address before proceeding to payment.')
        return redirect('core:checkout', item_id=item_id)

def remove_cart_items(session):
    CartItem.objects.filter(id=session['metadata']['item_id'], user__id=session['metadata']['user_id']).delete()


# @csrf_exempt
# def stripe_webhook(request):
#     payload = request.body
#     sig_header = request.META['HTTP_STRIPE_SIGNATURE']
#     event = None

#     try:
#         event = stripe.Webhook.construct_event(
#         payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
#     )
#     except ValueError as e: 
#         return HttpResponse(status=400)
#     except stripe.error.SignatureVerificationError as e:
#         return HttpResponse(status=400)

#     if event['type'] == 'checkout.session.completed':
#         session = stripe.checkout.Session.retrieve(event['data']['object']['id'])
#         customer_email = session['customer_details']['email']
#         customer_product = session['metadata']['item_name']
#         user_id = session['metadata']['user_id']
#         username = session['metadata']['userprofile']
#         user_profile = get_object_or_404(UserProfile, user__username=username)
#         cart_item = get_object_or_404(CartItem, id=session['metadata']['item_id'], user__id=user_id)
        
#         order = Order.objects.get(user__id=user_id, cart=cart_item)
#         order.order_status = 'Completed'
#         order.save()
#         print(user_profile)

#         payment = Payment.objects.create(user=user_profile, payment_method='CreditCard', payment_amount=cart_item.calculate_item_price())
#         payment.payment_bool = True
#         payment.save()


#         remove_cart_items(session=session)

#         subject = f'Payment Successful for {customer_product}'
#         message = f'Thank you for your purchase. Your payment for {customer_product} was successful.'
#         from_email = settings.DEFAULT_FROM_EMAIL
#         recipient_list = [customer_email]

#         send_mail(subject, message, from_email, recipient_list)

#     return HttpResponse(status=200)


def checkout_success(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return redirect('core:cancel')

    try:
        payment_session = stripe.checkout.Session.retrieve(session_id)
        item_id = payment_session.metadata.get('item_id')

        CartItem.objects.filter(id=item_id, user=request.user.userprofile).delete()

        return render(request, 'success.html')
    except stripe.error.StripeError as e:
        return redirect('core:cancel')



def checkout_cancel(request):
    return render(request, 'cancel.html')

