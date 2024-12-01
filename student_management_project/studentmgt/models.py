from django.db import models

from coursemgt.models import Course

class Student(models.Model):
    st_id = models.AutoField(primary_key=True)  # Auto-incrementing primary key
    fname = models.CharField(max_length=255)
    lname = models.CharField(max_length=255)
    dob = models.DateField()
    gender = models.CharField(max_length=1)
    st_email = models.EmailField()
    pr_email = models.EmailField()
    phone = models.CharField(max_length=20)
    pr_phone = models.CharField(max_length=20)
    address = models.TextField()
    courses = models.ManyToManyField(Course, related_name='students')
    batch_mon = models.CharField(max_length=255)
    batch_year = models.IntegerField()

    def __str__(self):
        return f"{self.fname} {self.lname}"

