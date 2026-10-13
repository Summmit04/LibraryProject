from django import forms
from .models import StudentProfile
from django import forms
from .models import IssuedBook

class IssueBookForm(forms.ModelForm):
    class Meta:
        model = IssuedBook
        fields = ['student', 'book', 'expiry_date']
        widgets = {
            'expiry_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

class StudentForm(forms.ModelForm):
    name = forms.CharField(max_length=100, label="Student Name")
    email = forms.EmailField(required=False, label="Email Address")

    class Meta:
        model = StudentProfile
        fields = ['roll_number', 'student_class', 'mobile_number']