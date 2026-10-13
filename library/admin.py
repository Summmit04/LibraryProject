from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Book, IssuedBook, StudentProfile, Category, Author
admin.site.register(Book)
admin.site.register(IssuedBook)
admin.site.register(Author)

class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Library Profile Details'
    fk_name = 'user'  

class UserAdmin(BaseUserAdmin):
    inlines = (StudentProfileInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super().get_inline_instances(request, obj)
    
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Category)

