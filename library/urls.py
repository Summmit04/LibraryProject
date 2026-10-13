from django.urls import path
from . import views

urlpatterns = [

    path('', views.admin_dashboard, name='admin_dashboard'),
    path('manage-books/', views.manage_books, name='manage_books'),
    path('issued-books/', views.manage_issued_books, name='manage_issued_books'),
    path('issue-book/', views.issue_book, name='issue_book'),
    path('book/<int:book_id>/', views.book_detail, name='book_detail'),
    path('profile/', views.student_profile, name='student_profile'),
    path('admin-student/<int:student_id>/', views.admin_student_profile, name='admin_student_profile'),
    path('students/', views.manage_students, name='manage_students'),
    path('delete-book/<int:book_id>/', views.delete_book, name='delete_book'),

    path('login/', views.user_login, name='user_login'),
    path('register/', views.register, name='register'),
    path('logout/', views.user_logout, name='user_logout'),
    path('book-issued-success/', views.book_issued_success, name='book_issued_success'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/delete/<int:pk>/', views.delete_student, name='delete_student'),
]