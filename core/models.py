from django.db import models
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from django.utils.text import slugify
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_countries.fields import CountryField

# Create your models here.


def validate_pfp_image_dimensions(image):
    width = image.width
    height = image.height

    if width != 300 or height != 300:
        raise ValidationError(f"Image dimensions must be 300x300 pixels. Current dimensions: {width}x{height}")




class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', default='profile_pictures/default_pfp.png')

    def __str__(self):
        return self.user.username

class CartItem(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    color = models.ForeignKey('Color', on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    size = models.ForeignKey('Size', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.title} ({self.color})"

    def calculate_item_price(self):
        return self.product.price * self.quantity

class Order(models.Model):
    cart = models.ForeignKey('CartItem', on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True)
    billing_address = models.ForeignKey('Address', related_name='checkout_billing_address', on_delete=models.SET_NULL, null=True)
    payment = models.ForeignKey('Payment', on_delete=models.SET_NULL, null=True)
    order_note = models.TextField(max_length=500, blank=True, null=True)
    order_status = models.CharField(max_length=50, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.id} - User: {self.user}, Status: {self.order_status}, Created at: {self.created_at}"
        
    def calculate_total_price(self):
        total_price = sum(item.calculate_item_price() for item in self.cart.all())
        return total_price



class Address(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    street_address = models.CharField(max_length=255)
    apartment_address = models.CharField(max_length=255, blank=True)
    zip_code = models.CharField(max_length=10)
    country = models.CharField(max_length=200, choices=CountryField(multiple=False).choices)
    default = models.BooleanField(default=False)

    def __str__(self):
        return f"Address of {self.user.user.username}"

class Payment(models.Model):
    PAYMENT_CHOICES = (
        ('Stripe', 'Stripe'),
        ('PayPal', 'PayPal'),
    )
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    payment_method = models.CharField(choices=PAYMENT_CHOICES, max_length=14)
    payment_bool = models.BooleanField(default=False)
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment by {self.user.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


def validate_slideshow_image_dimensions(image):
    width = image.width

    if width != 1920:
        raise ValidationError(f"Image dimensions must be 1920 pixels. Current dimensions: {width}")

class Slideshow(models.Model):
    background_image = models.ImageField(upload_to='slideshow/', validators=[validate_slideshow_image_dimensions])
    banner_title = models.CharField(max_length=100)
    brief_description = models.CharField(max_length=110)
    button_text = models.CharField(max_length=50)

    def __str__(self):
        return self.banner_title

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Color(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Product(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    price = models.IntegerField(validators=[
            MaxValueValidator(9999999),
            MinValueValidator(0),
        ])
    description = models.TextField()
    additional_information = models.TextField(blank=True, null=True)
    color = models.ManyToManyField('Color')
    sizes = models.ManyToManyField('Size', blank=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, null=True)
    tags = TaggableManager()
    
    is_clothing = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(null=False)

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            unique_slug = base_slug
            num = 1
            while Product.objects.filter(slug=unique_slug).exists():
                unique_slug = f"{base_slug}-{num}"
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)


def validate_product_image_dimensions(image):
    width = image.width

    if width < 600 or width > 800:
        raise ValidationError(f"Image dimensions must be 700 pixels. Current dimensions: {width}")

class Image(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    images = models.ImageField(upload_to='product-images/', validators=[validate_product_image_dimensions])

    def __str__(self):
        return f'Image for {self.product_id}'

class Review(models.Model):
    product = models.ForeignKey('Product', on_delete=models.CASCADE)
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    content = models.CharField(max_length=200)
    rating = models.IntegerField(validators=[MaxValueValidator(5), MinValueValidator(1),])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Review by {self.user.user.username} for {self.product.title}"
