from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('library', '0002_book_cover_image'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='description',
            field=models.TextField(blank=True, help_text='Enter a detailed summary of the book', null=True),
        ),
    ]
