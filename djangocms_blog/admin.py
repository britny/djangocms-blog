# -*- coding: utf-8 -*-
from copy import deepcopy
from cms.admin.placeholderadmin import FrontendEditableAdminMixin, \
    PlaceholderAdminMixin
from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import get_user_model
from parler.admin import TranslatableAdmin
from django.contrib.sites.models import Site

from .models import BlogCategory, Post
from .settings import get_setting

try:
    from admin_enhancer.admin import EnhancedModelAdminMixin
except ImportError:
    class EnhancedModelAdminMixin(object):
        pass


class BlogCategoryAdmin(EnhancedModelAdminMixin, TranslatableAdmin):
    exclude = ['parent']

    _fieldsets = [
        (None, {
            'fields': [('name', 'slug')]
        }),
        ('Info', {
            'fields': ([], ),
            'classes': ('collapse',)
        }),
    ]

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('name',)}

    def get_queryset(self, request):
        current_site = Site.objects.get_current()
        return BlogCategory.objects.filter(sites=current_site)

    def get_fieldsets(self, request, obj=None):
        fsets = deepcopy(self._fieldsets)
        if get_setting('MULTISITE'):
            fsets[1][1]['fields'][0].append('sites')
        return fsets

    def save_related(self, request, form, formsets, change):
        if not form.cleaned_data['sites']:
            form.cleaned_data['sites'] = [Site.objects.get_current()]
        super(BlogCategoryAdmin, self).save_related(
            request, form, formsets, change)

    class Media:
        css = {
            'all': ('%sdjangocms_blog/css/%s' % (settings.STATIC_URL,
                                                 'djangocms_blog_admin.css'),)
        }


# from django.contrib import admin
# from django.utils.translation import ugettext_lazy as _

# class SitesFilter(admin.SimpleListFilter):
#     title = _('Site')
#     parameter_name = 'sites'
#
#     def lookups(self, request, model_admin):
#         return (('current_site', _('Current Site')),)
#
#     def queryset(self, request, queryset):
#         if self.value() == 'current_site':
#             return queryset.filter(sites__in=[Site.objects.get_current()])
#         else:
#             return queryset


class PostAdmin(EnhancedModelAdminMixin, FrontendEditableAdminMixin,
                PlaceholderAdminMixin, TranslatableAdmin):
    list_display = ['title', 'author', 'date_published', 'date_published_end']
    # list_filter = (SitesFilter,)
    date_hierarchy = 'date_published'
    raw_id_fields = ['author']
    frontend_editable_fields = ('title', 'abstract', 'post_text')
    enhance_exclude = ('main_image', 'tags')
    _fieldsets = [
        (None, {
            'fields': [('title', 'categories', 'publish')]
        }),
        ('Info', {
            'fields': (['slug', 'tags'],
                       ('date_published', 'date_published_end', 'enable_comments')),
            'classes': ('collapse',)
        }),
        ('Images', {
            'fields': (('main_image', 'main_image_thumbnail', 'main_image_full'),),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': [('meta_description', 'meta_title', 'meta_keywords')],
            'classes': ('collapse',)
        }),
    ]

    def formfield_for_dbfield(self, db_field, **kwargs):
        field = super(PostAdmin, self).formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == 'meta_description':
            original_attrs = field.widget.attrs
            original_attrs['maxlength'] = 160
            field.widget = forms.TextInput(original_attrs)
        elif db_field.name == 'meta_title':
            field.max_length = 70
        return field

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == "categories":
            kwargs["queryset"] = BlogCategory.objects.filter(
                sites=Site.objects.get_current())
        return super(PostAdmin, self).formfield_for_manytomany(
            db_field, request, **kwargs)

    def get_fieldsets(self, request, obj=None):
        fsets = deepcopy(self._fieldsets)
        if get_setting('USE_ABSTRACT'):
            fsets[0][1]['fields'].append('abstract')
        if not get_setting('USE_PLACEHOLDER'):
            fsets[0][1]['fields'].append('post_text')
        if get_setting('MULTISITE'):
            fsets[1][1]['fields'][0].append('sites')
        if request.user.is_superuser:
            fsets[1][1]['fields'][0].append('author')
        return fsets

    def get_prepopulated_fields(self, request, obj=None):
        return {'slug': ('title',)}

    def get_queryset(self, request):
        current_site = Site.objects.get_current()
        return Post.objects.filter(sites=current_site)

    def save_model(self, request, obj, form, change):
        if not obj.author_id and get_setting('AUTHOR_DEFAULT'):
            if get_setting('AUTHOR_DEFAULT') is True:
                user = request.user
            else:
                user = get_user_model().objects.get(username=get_setting('AUTHOR_DEFAULT'))
            obj.author = user
        super(PostAdmin, self).save_model(request, obj, form, change)

    def save_related(self, request, form, formsets, change):
        if not form.cleaned_data['sites']:
            form.cleaned_data['sites'] = [Site.objects.get_current()]
        super(PostAdmin, self).save_related(request, form, formsets, change)

    class Media:
        css = {
            'all': ('%sdjangocms_blog/css/%s' % (settings.STATIC_URL,
                                                 'djangocms_blog_admin.css'),)
        }


admin.site.register(BlogCategory, BlogCategoryAdmin)
admin.site.register(Post, PostAdmin)
