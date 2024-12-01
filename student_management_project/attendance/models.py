# from django.db import models
# from studentmgt.models import Student

# class Attendance(models.Model):
#     st_id = models.ForeignKey(Student, on_delete=models.CASCADE)
#     date = models.DateField()
#     status = models.CharField(max_length=1, choices=[('P', 'Present'), ('A', 'Absent')])

#     def __str__(self):
#         return f"Attendance for {self.st_id} on {self.date}"
