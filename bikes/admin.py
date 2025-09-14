from django.contrib import admin
from django.utils.html import format_html
from .models import Bike,FeatureSection, BikeForSale, Testimonial, RiderTrustSection, AboutSection, MissionSection
from .models import ApproachSection, ApproachImage


@admin.register(FeatureSection)
class FeatureSectionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "image_preview")

    def image_preview(self, obj):
        if obj.image:
            return format_html("<img src='{}' width='60' height='40' style='object-fit:cover;' />", obj.image.url)
        return "No Image"
    image_preview.short_description = "Image"


@admin.register(Bike)
class BikeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "image_preview")  # show columns in admin list
    search_fields = ("name",)  # enable search by name

    def image_preview(self, obj):
        if obj.image:
            return format_html("<img src='{}' width='60' height='40' style='object-fit:cover;' />", obj.image.url)
        return "No Image"
    image_preview.short_description = "Image"

# testimonial
@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ("name", "role", "message")   # show these fields in admin list view
    search_fields = ("name", "role", "message")


@admin.register(RiderTrustSection)
class RiderTrustSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "description")


# aboutpage
@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "description")

@admin.register(MissionSection)
class MissionSectionAdmin(admin.ModelAdmin):
    list_display = ("title", "description")

class ApproachImageInline(admin.TabularInline):
    model = ApproachImage
    extra = 1

@admin.register(ApproachSection)
class ApproachSectionAdmin(admin.ModelAdmin):
    inlines = [ApproachImageInline]
    list_display = ("title",)

# cutomer review contact page
@admin.register(BikeForSale)
class BikeForSaleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "thumbnail",      # custom image preview
        "name",
        "brand",
        "year",
        "cc",
        "model_variant",
        "formatted_price",
        "formatted_km",
        "fuel_type",
        "owner_number",
        "location",
        "is_featured",
        "is_active",
        "created_at",
    )
    list_filter = (
        "fuel_type",
        "owner_number",
        "brand",
        "year",
        "is_featured",
        "is_active",
        "location",
    )
    search_fields = ("name", "brand", "location", "model_variant")
    list_editable = ("is_featured", "is_active")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 20

    # Show a small image preview in admin list
    def thumbnail(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="80" height="50" style="object-fit:cover;border-radius:5px;" />'
        return "No Image"
    thumbnail.allow_tags = True
    thumbnail.short_description = "Image"


from .models import AuthImage

@admin.register(AuthImage)
class AuthImageAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "is_for_login", "is_for_register", "uploaded_at")
    list_filter = ("is_for_login", "is_for_register")
    search_fields = ("title",)

from .models import Motorcycle

@admin.register(Motorcycle)
class MotorcycleAdmin(admin.ModelAdmin):
    list_display = ('brand', 'model', 'variant', 'year', 'kms_driven', 'owner', 'estimated_price')
    list_filter = ('brand', 'year', 'owner')
    search_fields = ('brand', 'model', 'variant')
