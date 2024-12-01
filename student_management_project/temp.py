from attendance.models import Attendance
from django.utils import timezone

today = timezone.now().date()
Attendance.objects.filter(date=today, status='P').count()
