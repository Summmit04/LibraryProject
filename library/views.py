from django.db import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Book, Category, Author, IssuedBook
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
import json
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta

@login_required
def admin_dashboard(request):

    total_books = Book.objects.count()
    total_students = User.objects.filter(is_superuser=False).count()
    issued_books_count = IssuedBook.objects.filter(is_returned=False).count()
 
    today = timezone.now().date()
    overdue_books_count = IssuedBook.objects.filter(expiry_date__lt=today, is_returned=False).count()
    
    categories = Category.objects.annotate(book_count=Count('book'))
    category_names = [cat.name for cat in categories]
    category_counts = [cat.book_count for cat in categories]

    days_labels = []
    weekly_issued_counts = []
    
    for i in range(6, -1, -1):
        target_date = today - timedelta(days=i)
        days_labels.append(target_date.strftime('%a')) 
        
        count = IssuedBook.objects.filter(issue_date=target_date).count()
        weekly_issued_counts.append(count)

    context = {
        'total_books': total_books,
        'total_students': total_students,
        'issued_books_count': issued_books_count,
        'overdue_books_count': overdue_books_count,  
        'category_labels': json.dumps(category_names),
        'category_data': json.dumps(category_counts),
        'days_labels': json.dumps(days_labels),
        'weekly_issued_counts': json.dumps(weekly_issued_counts),
    }
    
    return render(request, 'library/admin_dashboard.html', context)

def manage_books(request):
    query = request.GET.get('search_query', '')
    category_id = request.GET.get('category', '')
    availability = request.GET.get('availability', '')

    books = Book.objects.all()

    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__name__icontains=query))

    if category_id:
        books = books.filter(category_id=category_id)

    if availability:
        if availability == 'available':
            books = books.filter(copies_available__gt=0)
        elif availability == 'out_of_stock':
            books = books.filter(copies_available=0)

    categories = Category.objects.all()

    context = {
        'books': books,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'selected_availability': availability,
    }
    return render(request, 'library/manage_books.html', context)

@login_required


def issue_book(request):
    students = User.objects.filter(is_staff=False)
    books = Book.objects.filter(copies_available__gt=0)

    if request.method == 'POST':
        student_id = request.POST.get('student')
        book_id = request.POST.get('book')

        if student_id and book_id:
            student = get_object_or_404(User, id=student_id)
            book = get_object_or_404(Book, id=book_id)

            if book.copies_available > 0:
                expiry = timezone.now().date() + timedelta(days=14)
                
            
                IssuedBook.objects.create(
                    student=student, 
                    book=book, 
                    expiry_date=expiry,
                    fine=0.00
                )
                return redirect('book_issued_success')

    context = {
        'students': students,
        'books': books
    }
    return render(request, 'library/issue_book.html', context)

def book_issued_success(request):
    return render(request, 'library/book_issued_success.html')

@login_required
def manage_issued_books(request):

    status = request.GET.get('status', '')
    issued_books = IssuedBook.objects.all().order_by('-issue_date')
    
    if status == 'overdue':
        today = timezone.now().date()
        issued_books = issued_books.filter(expiry_date__lt=today, is_returned=False)
        
    return render(request, 'library/manage_issued_books.html', {'issued_books': issued_books, 'status': status})

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('admin_dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'library/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)

                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                return redirect('admin_dashboard') 
    else:
        form = AuthenticationForm()
    return render(request, 'library/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('user_login')

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    return render(request, 'library/book_detail.html', {'book': book})

def student_profile(request, student_id):
    student = get_object_or_404(User, id=student_id)
    borrowed_books = IssuedBook.objects.filter(student=student).order_by('-issue_date')
    return render(request, 'library/student_profile.html', {'student': student, 'borrowed_books': borrowed_books})

def manage_students(request):
    students = User.objects.filter(is_staff=False)
    context = {'students': students}
    return render(request, 'library/manage_students.html', context)

def delete_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    title = book.title 
    book.delete()
    messages.success(request, f'"{title}" was successfully deleted from inventory.')
    return redirect('manage_books')