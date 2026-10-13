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
from .forms import StudentForm
from django.db import transaction
from .models import StudentProfile
from .forms import IssueBookForm

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
    if request.method == 'POST':
        student_id = request.POST.get('student')
        book_id = request.POST.get('book')
        expiry_date = request.POST.get('expiry_date')
        
        student_user = get_object_or_404(User, id=student_id)
        book_obj = get_object_or_404(Book, id=book_id)
        
        
        IssuedBook.objects.create(
            student=student_user,
            book=book_obj,
            expiry_date=expiry_date
        )
        
        
        if hasattr(book_obj, 'copies_available') and book_obj.copies_available > 0:
            book_obj.copies_available -= 1
            book_obj.save()
            
        return redirect('manage_issued_books')
        
    
    students = StudentProfile.objects.select_related('user').all()
    books = Book.objects.all()
    
    context = {
        'students': students,
        'books': books,
    }
    return render(request, 'library/issue_book.html', context)

@login_required
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

@login_required
def student_profile(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    borrowed_books = IssuedBook.objects.filter(student=request.user).order_by('-issue_date')
    return render(request, 'library/student_profile.html', {
        'profile': profile, 
        'student': request.user, 
        'borrowed_books': borrowed_books
    })

@login_required
def admin_student_profile(request, student_id):
    student_user = get_object_or_404(User, id=student_id)
    profile = get_object_or_404(StudentProfile, user=student_user)
    borrowed_books = IssuedBook.objects.filter(student=student_user).order_by('-issue_date')
    return render(request, 'library/student_profile.html', {
        'profile': profile, 
        'student': student_user,  
        'borrowed_books': borrowed_books
    })

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


@login_required
def add_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data.get('email', '')
            
            
            base_username = name.lower().replace(' ', '_')
            username = base_username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}_{counter}"
                counter += 1
                
            try:
                with transaction.atomic():
                   
                    user = User.objects.create_user(
                        username=username, 
                        email=email, 
                        first_name=name
                    )
                    user.set_unusable_password()
                    user.save()
                    
                 
                    profile, created = StudentProfile.objects.get_or_create(user=user)
                    profile.roll_number = form.cleaned_data.get('roll_number')
                    profile.student_class = form.cleaned_data.get('student_class')
                    profile.mobile_number = form.cleaned_data.get('mobile_number')
                    profile.save()
                    
                return redirect('manage_students')
            except Exception as e:
                form.add_error(None, f"Error saving student: {e}")
    else:
        form = StudentForm()
    return render(request, 'library/add_student.html', {'form': form})

from django.shortcuts import get_object_or_404

@login_required
def delete_student(request, pk):
    profile = get_object_or_404(StudentProfile, pk=pk)
   
    if profile.user:
        profile.user.delete()
    else:
        profile.delete()
    return redirect('manage_students')

@login_required
def issue_book(request):
    if request.method == 'POST':
        form = IssueBookForm(request.POST)
        if form.is_valid():
            book_issue = form.save(commit=False)
            
            
            book_obj = book_issue.book
            if hasattr(book_obj, 'copies_available') and book_obj.copies_available > 0:
                book_obj.copies_available -= 1
                book_obj.save()
                
            book_issue.save()
            return redirect('manage_issued_books') 
    else:
        form = IssueBookForm()
        
    
    students = StudentProfile.objects.select_related('user').filter(user__is_superuser=False, user__is_staff=False)
    books = Book.objects.all()
    
    context = {
        'form': form,
        'students': students,
        'books': books,
    }
    return render(request, 'library/issue_book.html', context)