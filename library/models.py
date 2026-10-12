from django.db import models
from django.contrib.auth.models import User
from datetime import datetime, timedelta, date
from django.db.models.signals import post_save
from django.dispatch import receiver


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Author(models.Model):
    name = models.CharField(max_length=150, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Book(models.Model):
    title = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    isbn_number = models.CharField(max_length=13, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    copies_available = models.PositiveIntegerField(default=1)
    cover_image = models.ImageField(upload_to='book_covers/', null=True, blank=True)
    description = models.TextField(blank=True, null=True, help_text="Enter a detailed summary of the book")
    is_active = models.BooleanField(default=True)
    added_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

def get_expiry_date():
    return datetime.today() + timedelta(days=14)


class IssuedBook(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    issue_date = models.DateField(auto_now_add=True)
    expiry_date = models.DateField()
    is_returned = models.BooleanField(default=False)
    fine = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)

    def calculate_fine(self):
        if self.is_returned:
            return 0.00
        
        today = date.today()
        if today > self.expiry_date:
            overdue_days = (today - self.expiry_date).days
            fine_per_day = 1.00
            return overdue_days * fine_per_day
            
        return 0.00


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, blank=True, null=True)
    student_class = models.CharField(max_length=50, blank=True, null=True)
    mobile_number = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        StudentProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.studentprofile.save()

@receiver(post_save, sender=IssuedBook)
def decrease_book_stock(sender, instance, created, **kwargs):
    if created:
        instance.book.copies_available -= 1
        instance.book.save()