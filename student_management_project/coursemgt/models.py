from django.db import models

# Create your models here.
class Course(models.Model):
    c_id = models.TextField(primary_key=True)
    cname = models.CharField(max_length=255)
    cduration = models.IntegerField()

    def __str__(self):
        return self.cname
    
class Subject(models.Model):
    sb_id = models.TextField(primary_key=True)
    sbname = models.CharField(max_length=255)
    courses = models.ManyToManyField(Course, related_name='subjects')

    def __str__(self):
        return self.sbname