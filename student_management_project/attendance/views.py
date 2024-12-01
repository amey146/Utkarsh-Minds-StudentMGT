import csv
from io import BytesIO
import os
from turtle import pd
from django.shortcuts import redirect, render, HttpResponse
from django.utils import timezone
from matplotlib import pyplot as plt
from studentmgt.models import Student, Course
from django.core.mail import send_mail
from django.conf import settings
from datetime import date, timedelta
from django.urls import reverse

def attendance_home(request):
    return render(request, "attendance/attendance_home.html")

def attendance_add(request):
    courses = Course.objects.all()
    selected_course = request.GET.get('course')
    selected_batch = request.GET.get('batch')
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')

    # to set a default course if no course is selected
    if not selected_course and courses.exists():
        selected_course = courses.first().c_id

    # get distinct batch months and years for the selected course
    if selected_course:
        batches = Student.objects.filter(courses__c_id=selected_course).values('batch_mon', 'batch_year').distinct()
    else:
        batches = Student.objects.values('batch_mon', 'batch_year').distinct()

    # filter students based on selected course, month, and year
    students_query = Student.objects.filter(courses__c_id=selected_course)

    if selected_batch:
        batch_mon, batch_year = selected_batch.split('-')
        students_query = students_query.filter(batch_mon=batch_mon, batch_year=batch_year)

    if selected_month and selected_year:
        students_query = students_query.filter(batch_mon=selected_month, batch_year=selected_year)

    # Fetch students after applying the course and date filters
    students = students_query.all()

    return render(request, "attendance/attendance_add.html", {
        'courses': courses,
        'students': students,
        'selected_course': selected_course,
        'batches': batches,
        'selected_batch': selected_batch,
        'selected_month': selected_month,
        'selected_year': selected_year,
    })



def attendance_add_action(request):
    today = timezone.now().date()

    if request.method == 'POST':
        attendance_data = []
        for key, value in request.POST.items():
            if key.startswith('status_'):
                student_id = key.split('_')[1]
                status = value
                student = Student.objects.get(pk=student_id)
                course = student.courses.all()
                batch = student.batch_mon+"_"+str(student.batch_year)
                # Collect attendance data to save in CSV
                attendance_data.append([student_id, student.fname+" "+student.lname, status, today])
                save_individual_attendance_to_csv(student_id, student.fname+" "+student.lname, course[0], batch, status, today)
        
        # Save the attendance data to CSV
        save_attendance_to_csv(attendance_data, course[0], batch)

        # Call the function to send emails to absent students
        send_absent_email(request)

        return render(request, 'attendance/emailsent.html')

    students = Student.objects.all()
    return render(request, 'attendance.html', {'students': students})




# Function to save attendance to CSV
def save_individual_attendance_to_csv(student_id, student_name, cname, batch, status, date):
    #roll id wise new file
    new_file_start = student_id
    # Specify the subdirectory 'individual_attendance'
    attendance_dir = os.path.join(settings.MEDIA_ROOT, 'individual_attendance')
    
    # Ensure the directory exists
    if not os.path.exists(attendance_dir):
        os.makedirs(attendance_dir)

    filename = f'{cname}_{batch}_attendance_id_{new_file_start}.csv'
    filepath = os.path.join(attendance_dir, filename)
    
    # Create the CSV if it doesn't exist, or append if it does
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Write the header only if the file is new
        if not file_exists:
            writer.writerow(['Student ID', 'Name', 'Status', 'Date'])

        # Write attendance data
        writer.writerow([student_id, student_name, status, date])






# Function to save attendance to CSV
def save_attendance_to_csv(attendance_data, cname, batch):
    new_file_start = get_day_start()
    # Specify the subdirectory 'attendance'
    attendance_dir = os.path.join(settings.MEDIA_ROOT, 'attendance')
    
    # Ensure the directory exists
    if not os.path.exists(attendance_dir):
        os.makedirs(attendance_dir)

    filename = f'{cname}_{batch}_attendance_{new_file_start}.csv'
    filepath = os.path.join(attendance_dir, filename)
    
    # Create the CSV if it doesn't exist, or append if it does
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Write the header only if the file is new
        if not file_exists:
            writer.writerow(['Student ID', 'Name', 'Status', 'Date'])

        # Write attendance data
        for record in attendance_data:
            writer.writerow(record)



def attendance_list(request):
    search_query = request.GET.get('search', '')

    # Update the path to include 'attendance' subdirectory
    media_root = os.path.join(settings.MEDIA_ROOT, 'attendance')
    csv_files = []

    try:
        if os.path.exists(media_root):
            for file in os.listdir(media_root):
                if file.endswith('.csv'):
                    # Validate the file as a CSV
                    try:
                        with open(os.path.join(media_root, file), 'r') as f:
                            reader = csv.reader(f)
                            next(reader)  # Skip header row
                            if search_query.lower() in file.lower():  # Case-insensitive search
                                csv_files.append(file)
                    except csv.Error:
                        print(f"Invalid CSV file: {file}")
                    except Exception as e:  # Catch other potential errors
                        print(f"Error processing file {file}: {e}")
            else:
                print("Attendance folder not found")
    except FileNotFoundError:
        print("Attendance folder not found")

 



    # Generate download URLs (assuming you have a download view)
    file_urls = [reverse('attendance_download_csv',kwargs={'file_name': file, 'dir_name': 'attendance'}) for file in csv_files]
    delete_urls = [reverse('attendance_delete_csv', kwargs={'file_name': file, 'dir_name': 'attendance'}) for file in csv_files]



    zipped_files = list(zip(csv_files, file_urls, delete_urls))
    context = {'zipped_files': zipped_files}
    return render(request, 'attendance/attendance_list.html', context)


def ind_attendance_list(request):
    search_query = request.GET.get('search', '')

    # Update the path to include 'attendance' subdirectory
    media_root = os.path.join(settings.MEDIA_ROOT, 'individual_attendance')
    csv_files = []

    try:
        if os.path.exists(media_root):
            for file in os.listdir(media_root):
                if file.endswith('.csv'):
                    # Validate the file as a CSV
                    try:
                        with open(os.path.join(media_root, file), 'r') as f:
                            reader = csv.reader(f)
                            next(reader)  # Skip header row
                            if search_query.lower() in file.lower():  # Case-insensitive search
                                csv_files.append(file)
                    except csv.Error:
                        print(f"Invalid CSV file: {file}")
                    except Exception as e:  # Catch other potential errors
                        print(f"Error processing file {file}: {e}")
            else:
                print("Attendance folder not found")
    except FileNotFoundError:
        print("Attendance folder not found")

    # Generate download URLs (assuming you have a download view)
    file_urls = [reverse('attendance_download_csv', kwargs={'file_name': file, 'dir_name': 'individual_attendance'}) for file in csv_files]
    delete_urls = [reverse('attendance_delete_csv', kwargs={'file_name': file, 'dir_name': 'individual_attendance'}) for file in csv_files]
    zipped_files = list(zip(csv_files, file_urls, delete_urls))
    context = {'zipped_files': zipped_files}
    return render(request, 'attendance/ind_attendance_list.html', context)


def download_csv(request, file_name, dir_name):
    # Update to include 'attendance' subdirectory
    media_root = os.path.join(settings.MEDIA_ROOT, dir_name)
    file_path = os.path.join(media_root, file_name)
    print(media_root)
    print(file_path)
    try:
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    except FileNotFoundError:
        return HttpResponse('File not found', status=404)
    except PermissionError:
        return HttpResponse('Permission denied', status=403)


def delete_csv(request, file_name, dir_name):
    # Update to include 'attendance' subdirectory
    media_root = os.path.join(settings.MEDIA_ROOT, dir_name)
    file_path = os.path.join(media_root, file_name)
    try:
        os.remove(file_path)
        return redirect('attendance_list')  # Redirect to the list view after deletion
    except FileNotFoundError:
        return HttpResponse('File not found', status=404)
    except PermissionError:
        return HttpResponse('Permission denied', status=403)













def send_absent_email(request):
    today = date.today()
    formatted_date = today.strftime("%d-%m-%Y")

    # Fetch all students marked as 'Absent' from the POST data
    absent_students = []
    for key, value in request.POST.items():
        if key.startswith('status_') and value == 'A':
            student_id = key.split('_')[1]
            student = Student.objects.get(pk=student_id)
            absent_students.append(student)

    # Loop through each absent student and send an email
    for student in absent_students:
        guardian_email = student.pr_email  # Use the `pr_email` field from the Student model
        student_name = f"{student.fname} {student.lname}"  # Combine first and last names
        
        # Format the message with the student's name
        message = f'''Dear Parent/Guardian,
This is to inform you that your ward, {student_name}, was absent for class today, {formatted_date}.
Please contact us if you have any questions.

Thank you,
Utkarsh Minds
E-mail: pranav.nerurkar@utkarshminds.com
Phone: +91 (0) 961-999-7797
Fax: +91 (0) 456 7891 
'''

        send_mail(
            subject='Attendance Report',
            message=message,
            from_email='settings.EMAIL_HOST_USER',
            recipient_list=[guardian_email],
            fail_silently=False
        )
    
    return render(request, 'attendance/emailsent.html')







# Utility function to get the current week's Monday as the start of the week
def get_week_start():
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    return start_of_week

# def get_month_start():
#     today = timezone.now().date()
#     start_of_month = today.replace(day=1)
#     return start_of_month

def get_day_start():
    today = timezone.now()
    return today.strftime("%d_%m_%Y")








# from django.shortcuts import redirect, render, HttpResponse
# from django.utils import timezone
# from attendance.models import Attendance
# from studentmgt.models import Student, Course
# from django.core.mail import send_mail
# from django.conf import settings
# from datetime import date
    
# def attendance_home(request):
#     courses = Course.objects.all()
#     selected_course = request.GET.get('course')
#     today = timezone.now().date()

#     # Check if attendance for the selected course has already been marked today
#     if selected_course:
#         students = Student.objects.filter(courses__c_id=selected_course)
#         already_marked = Attendance.objects.filter(date=today, st_id__in=students).exists()
#     else:
#         students = Student.objects.all()
#         already_marked = Attendance.objects.filter(date=today).exists()

#     if already_marked:
#         # If attendance has been marked, show the attendance list
#         attendance_list = Attendance.objects.filter(date=today)
#         # Debugging purpose
#         # Attendance.objects.all().delete()
#         return render(request, "attendance/attendance_list.html", {
#             'attendance_list': attendance_list,
#             'selected_course': selected_course,
#         })

#     return render(request, "attendance/attendance_home.html", {
#         'courses': courses,
#         'students': students,
#         'selected_course': selected_course,
#     })

# def attendance_add(request):
#     today = timezone.now().date()

#     # Check if attendance has already been marked for today
#     already_marked = Attendance.objects.filter(date=today).exists()

#     if already_marked:
#         # Redirect or display a message indicating attendance is already marked
#         return HttpResponse("Attendance for today has already been recorded.")
#         # return render(request, 'attendance/emailsent.html')

#     if request.method == 'POST':
#         for key, value in request.POST.items():
#             if key.startswith('status_'):
#                 student_id = key.split('_')[1]
#                 status = value
#                 student = Student.objects.get(pk=student_id)
#                 # Save attendance for today
#                 Attendance.objects.create(st_id=student, date=today, status=status)
                
#         # Call the function to send emails to absent students
#         send_absent_email(request)

#         return render(request, 'attendance/emailsent.html')

#     students = Student.objects.all()
#     return render(request, 'attendance.html', {'students': students})


# def attendance_list(request):
#     today = timezone.now().date()
#     attendance_list = Attendance.objects.filter(date=today)
#     total_present = attendance_list.filter(status='P').count()  # Count the number of 'P' statuses
#     total_present = Attendance.objects.filter(date=today, status='A')
#     print(total_present)
#     return render(request, "attendance/attendance_list.html", {
#         'attendance_list': attendance_list,
#         'total_present': total_present
#     })

# from django.core.mail import send_mail
# from datetime import date
# from .models import Attendance, Student

# def send_absent_email(request):
#     if request.method == 'POST':
#         today = date.today()
#         formatted_date = today.strftime("%d-%m-%Y")

#         # Fetch all students marked as 'Absent' today
#         absent_students = Attendance.objects.filter(date=today, status='A')

#         # Loop through each absent student and send an email
#         for record in absent_students:
#             student = record.st_id
#             guardian_email = student.pr_email  # Use the `pr_email` field from the Student model
#             student_name = f"{student.fname} {student.lname}"  # Combine first and last names
            
#             # Format the message with the student's name
#             message = f'''Dear Parent/Guardian,
# This is to inform you that your ward, {student_name}, was absent from class today, {formatted_date}.
# Please contact us if you have any questions.

# Thank you,
# Utkarsh Minds
# E-mail: pranav.nerurkar@utkarshminds.com
# Phone: +91 (0) 961-999-7797
# Fax: +91 (0) 456 7891 
# '''

#             send_mail(
#                 subject='Attendance Report',
#                 message=message,
#                 from_email='settings.EMAIL_HOST_USER',
#                 recipient_list=[guardian_email],
#                 fail_silently=False
#             )
    
#     return render(request, 'attendance/emailsent.html')
