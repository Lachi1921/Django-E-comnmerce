from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Register your models here.

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False

class UserProfileAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserProfileAdmin)


admin.site.register(CartItem)
admin.site.register(Payment)
admin.site.register(Address)
admin.site.register(Slideshow)
admin.site.register([Product, Image])
admin.site.register(Category)
admin.site.register(Color)
admin.site.register(Size)
admin.site.register(Review)
admin.site.register(Order)
