from django.shortcuts import redirect, render, HttpResponse
from matplotlib.dates import relativedelta

from coursemgt.models import Course, Subject
from studentmgt.models import Student
from datetime import date, datetime, timedelta
from django.utils import timezone
import os
from django.core.mail import send_mail
from django.conf import settings
import csv
from django.urls import reverse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
from reportlab.lib.utils import ImageReader
from io import BytesIO
from django.core.mail import EmailMessage
import pandas as pd
from collections import defaultdict

# Create your views here.
def quiz_home(request):
    return render(request, "quizmgt/quiz_home.html")

def quiz_add(request):
    courses = Course.objects.all()
    return render(request, "quizmgt/quiz_add.html",{'courses':courses})

def subject_select(request, c_id):
    c=Course.objects.get(pk=c_id)
    subjects= c.subjects.all()
    return render(request, 'quizmgt/subject_select.html', {'c': c, 'subjects':subjects})

def student_list(request, c_id, sbname):
    # Get the Course instance by its ID (c_id)
    course = Course.objects.get(c_id=c_id)

    # Get all students enrolled in the given course
    students_query = Student.objects.filter(courses=course)

    # Get the selected batch from the request
    selected_batch = request.GET.get('batch')

    if selected_batch:
        batch_mon, batch_year = selected_batch.split('-')
        students_query = students_query.filter(batch_mon=batch_mon, batch_year=batch_year)

    students = students_query.all()

    # Fetch distinct batches for the selected course
    batches = Student.objects.filter(courses=course).values('batch_mon', 'batch_year').distinct()

    context = {
        'course': course,
        'sbname': Subject.objects.get(pk=sbname),
        'students': students,
        'batches': batches,
        'selected_batch': selected_batch,
    }
    return render(request, 'quizmgt/student_list.html', context)



def quiz_submit(request, sbname):
    today = timezone.now().date()

    if request.method == 'POST':
        total = request.POST.get("total")
        quiz_data = []
        for key, value in request.POST.items():
            if key.startswith('scoredmarks_'):
                student_id = key.split('_')[1]
                score = value
                student = Student.objects.get(pk=student_id)
                student_fname = student.fname
                student_lname = student.lname
                # Collect attendance data to save in CSV
                quiz_data.append([today, sbname, student_id, student_fname+" "+student_lname, score, total])
                batch = student.batch_mon+"_"+str(student.batch_year)

                # append_quiz_data function with the relevant parameters to save or update the student's quiz data in their respective CSV files
                append_quiz_data(today=today,sbname=sbname, student_id=student_id, student_fname=student_fname, student_lname=student_lname, score=score, total=total)

        # Save the attendance data to CSV
        save_scores_to_csv(quiz_data, sbname, batch)
        # Call the function to send emails to absent students
        send_quiz_email(request, total, sbname)
        # send_report_email(request)
        return render(request, 'quizmgt/emailsent.html')

    students = Student.objects.all()
    return render(request, "quizmgt/quiz_home.html")


# Function to save attendance to CSV
def save_scores_to_csv(quiz_data, sbname, batch):
    new_file_start = get_day_start()
    # Specify the subdirectory 'attendance'
    score_dir = os.path.join(settings.MEDIA_ROOT, 'quiz_score')
    
    # Ensure the directory exists
    if not os.path.exists(score_dir):
        os.makedirs(score_dir)

    filename = f'{sbname}_{batch}_quiz_{new_file_start}.csv'
    filepath = os.path.join(score_dir, filename)
    
    # Create the CSV if it doesn't exist, or append if it does
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode='a', newline='') as file:
        writer = csv.writer(file)
        
        # Write the header only if the file is new
        if not file_exists:
            writer.writerow(['Date', 'Subject', 'Student ID', 'Name', 'Score', 'Total'])

        # Write attendance data
        for record in quiz_data:
            writer.writerow(record)


def append_quiz_data(today, sbname, student_id, student_fname, student_lname, score, total):
    # Create the data to append
    data = {
        'Date': [today],
        'Subject': [sbname],
        'Student ID': [student_id],
        'Full Name': [f"{student_fname} {student_lname}"],
        'Score': [score],
        'Total': [total]
    }
    
    df = pd.DataFrame(data)

    # Define the filename based on student_id
    report_dir = os.path.join(settings.MEDIA_ROOT, 'report_score')
    filename = f"{student_id}.csv"
    filepath = os.path.join(report_dir, filename)

    
    if not os.path.exists(report_dir):
        os.makedirs(report_dir)

    file_exists = os.path.isfile(filepath)

    # Check if the file exists
    if file_exists:
        # If it exists, append the new data
        df.to_csv(filepath, mode='a', header=False, index=False)
    else:
        # If it doesn't exist, create it with header
        df.to_csv(filepath, index=False)


def dummy_send_quiz_email(request, total, sbname):
    return render(request, 'quizmgt/emailsent.html')


# Below Code works but disabled for testing
def send_quiz_email(request, total, sbname):
    today = date.today()
    formatted_date = today.strftime("%d-%m-%Y")

    # Fetch all students marked as 'Absent' from the POST data
    student_objects = []
    student_scores = []
    for key, value in request.POST.items():
        if key.startswith('scoredmarks_'):
            student_id = key.split('_')[1]
            student_scores.append(value)
            student = Student.objects.get(pk=student_id)
            student_objects.append(student)

    # Loop through each absent student and send an email
    for student, score in zip(student_objects, student_scores):

        guardian_email = student.pr_email  # Use the `pr_email` field from the Student model
        student_name = f"{student.fname} {student.lname}"  # Combine first and last names
        
        # Format the message with the student's name
        message = f'''Dear Parent/Guardian,

This is to inform you that your ward, {student_name}, has scored {score} out of {total} in {sbname} for today’s class.

Please contact us if you have any questions.

Thank you,
Utkarsh Minds
E-mail: pranav.nerurkar@utkarshminds.com
Phone: +91 (0) 961-999-7797
Fax: +91 (0) 456 7891
'''

        send_mail(
            subject='Quiz Score Report',
            message=message,
            from_email='settings.EMAIL_HOST_USER',
            recipient_list=[guardian_email],
            fail_silently=False
        )
    
    return render(request, 'quizmgt/emailsent.html')


def get_week_start():
    today = timezone.now().date()
    start_of_week = today - timedelta(days=today.weekday())
    return start_of_week

def get_month_start():
    today = timezone.now().date()
    month_name = today.strftime("%B")
    year = today.year
    return f"{month_name}_{year}"

def get_day_start():
    today = timezone.now()
    return today.strftime("%d_%m_%Y")

def quiz_list(request):
    search_query = request.GET.get('search', '')

    # Update the path to include 'attendance' subdirectory
    media_root = os.path.join(settings.MEDIA_ROOT, 'quiz_score')
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
                print("Quiz folder not found")
    except FileNotFoundError:
        print("Quiz folder not found")

    # Generate download URLs (assuming you have a download view)
    file_urls = [reverse('download_csv', kwargs={'file_name': file, 'dir_name': 'quiz_score'}) for file in csv_files]
    delete_urls = [reverse('delete_csv', kwargs={'file_name': file, 'dir_name': 'quiz_score'}) for file in csv_files]
    zipped_files = list(zip(csv_files, file_urls, delete_urls))
    context = {'zipped_files': zipped_files}
    return render(request, 'quizmgt/quiz_list.html', context)

def report_list(request):
    search_query = request.GET.get('search', '')

    # Update the path to include 'attendance' subdirectory
    media_root = os.path.join(settings.MEDIA_ROOT, 'report_score')
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
                print("Report folder not found")
    except FileNotFoundError:
        print("Report folder not found")

    # Generate download URLs (assuming you have a download view)
    file_urls = [reverse('download_csv', kwargs={'file_name': file, 'dir_name': 'report_score'}) for file in csv_files]
    delete_urls = [reverse('delete_csv', kwargs={'file_name': file, 'dir_name': 'report_score'}) for file in csv_files]
    zipped_files = list(zip(csv_files, file_urls, delete_urls))
    context = {'zipped_files': zipped_files}
    return render(request, 'quizmgt/report_list.html', context)


def report_generation(request):
    if is_new_month_start():
        students = Student.objects.all()
        # Loop through each student
        report_dir = os.path.join(settings.MEDIA_ROOT, 'report_score')
        current_date = datetime.now()
        # Subtract one month
        last_month_date = current_date - relativedelta(months=1)
        month = last_month_date.strftime('%m')
        response_string = "Reports generated successfully!\n\n"
        for student in students:
            total_scores = 0  # To hold the sum of scores across all subjects
            total_possible = 0  # To hold the sum of total possible scores across all subjects
            overall_percentage = 0
            # Generate the CSV file name for the current student
            csv_file_path = os.path.join(report_dir, f"{student.pk}.csv")
            subject_scores = extract_report_individual(csv_file_path, month)
            student_name = student.fname+" "+student.lname
            course_name = student.courses.first()

            total_scores = 0  # To hold the sum of scores across all subjects
            total_possible = 0  # To hold the sum of total possible scores across all subjects

            for subject, data in subject_scores.items():
                # response_string += f"Student: {student_name}, Subject: {subject}, Total Score: {data['scores']}, Total Possible: {data['totals']}\n"
                total_scores += data['scores']  # Accumulating total scores
                total_possible += data['totals']  # Accumulating total possible scores

            # Calculate overall percentage
            if total_possible > 0:  # Avoid division by zero
                overall_percentage = (total_scores / total_possible) * 100
                response_string += f"Overall Percentage: {overall_percentage:.2f}%\n"
            else:
                response_string += "Total possible score is zero, cannot calculate percentage.\n"

                

            pdf_buffer = generate_pdf(student_name=student_name,roll_number=student.st_id,course_name=course_name,course_percentage=overall_percentage,subject_scores=subject_scores)
            send_report_email(request=request,pdf_buffer=pdf_buffer,guardian_email=student.pr_email)
            
        return render(request, 'quizmgt/emailsent.html', {subject_scores})
    else:
        return HttpResponse("Sorry its not a month start today")



from datetime import datetime
def extract_report_individual(csv_file_path, month):
    # Dictionary to store scores and totals for each subject
    subject_scores = defaultdict(lambda: {'scores': 0, 'totals': 0})
    print("I am in extract")
    try:
        # Check if the file exists
        if not os.path.exists(csv_file_path):
            print(f"File not found: {csv_file_path}. Skipping...")
            return subject_scores
        
        # Open the CSV file and read its contents
        with open(csv_file_path, mode='r') as file:
            reader = csv.DictReader(file)

            for row in reader:
                print("I am in reader")
                # Convert the date from the row and extract the month
                date = datetime.strptime(row['Date'], '%Y-%m-%d')

                # Check if the month matches the one we're interested in
                if date.strftime('%m') == month:
                    subject = row['Subject']
                    score = int(row['Score'])
                    total = int(row['Total'])

                    # Add the score and total to the subject entry
                    subject_scores[subject]['scores'] += score
                    subject_scores[subject]['totals'] += total
                    print("I am in adding")

    except FileNotFoundError:
        print(f"File not found: {csv_file_path}. Skipping...")
    
    print("I am in returned", subject_scores.items())
    return subject_scores

def is_new_month_start():
    # Get today's date
    today = datetime.now()
    
    # Check if today is the first day of the month
    return today.day == 1


def download_csv(request, file_name, dir_name):
    # Update to include 'attendance' subdirectory
    media_root = os.path.join(settings.MEDIA_ROOT, dir_name)
    file_path = os.path.join(media_root, file_name)
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
        return redirect('quiz_list')  # Redirect to the list view after deletion
    except FileNotFoundError:
        return HttpResponse('File not found', status=404)
    except PermissionError:
        return HttpResponse('Permission denied', status=403)

# def generate_pdf(student_name, roll_number, course_name, course_percentage, subjects, final_grade, logo_path):
#     buffer = BytesIO()
#     p = canvas.Canvas(buffer, pagesize=A4)
#     width, height = A4
    
#     # Add logo (logo_path is the path to the logo image file)
#     if logo_path:
#         logo = ImageReader(logo_path)
#         p.drawImage(logo, 50, height - 100, width=100, height=50, preserveAspectRatio=True, mask='auto')
    
#     # Add institute header after the logo
#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(160, height - 50, "Utkarsh Minds")
#     p.setFont("Helvetica", 10)
#     p.drawString(160, height - 70, "E-mail: pranav.nerurkar@utkarshminds.com")
#     p.drawString(160, height - 85, "Phone: +91 (0) 961-999-7797 | Fax: +91 (0) 456 7891")
    
#     # Draw a horizontal line under the header and logo
#     p.setLineWidth(0.5)
#     p.line(50, height - 100, width - 50, height - 100)
    
#     # Add student name and roll number
#     p.setFont("Helvetica", 12)
#     p.drawString(100, height - 200, f"Student Name: {student_name}")
#     p.drawString(100, height - 220, f"Roll Number: {roll_number}")

#     # Title: Course information
#     p.setFont("Helvetica-Bold", 16)
#     p.drawString(100, height - 150, f"Course: {course_name}")
#     p.setFont("Helvetica", 12)
#     p.drawString(100, height - 170, f"Overall Percentage: {course_percentage}%")
    
#     # Table for subjects and percentages
#     data = [["Subject", "Percentage"]]
    
#     # Add subject data to the table
#     for subject_name, percentage in subjects.items():
#         data.append([subject_name, f"{percentage}%"])
    
#     # Create table
#     table = Table(data, colWidths=[200, 100])
#     table.setStyle(TableStyle([
#         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
#         ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#         ('FONTSIZE', (0, 0), (-1, -1), 12),
#         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#         ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
#         ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
#     ]))
    
#     # Place the table on the PDF
#     table.wrapOn(p, width, height)
#     table.drawOn(p, 100, height - 320)
    
#     # Final grade
#     p.setFont("Helvetica-Bold", 14)
#     p.drawString(100, height - 380, f"Final Grade: {final_grade}")
    
#     # Footer
#     yr = date.today()
#     p.setFont("Helvetica", 10)
#     p.drawString(100, 50, "Utkarsh Minds Institute | "+str(yr.year))
    
#     # Draw a horizontal line above the footer
#     p.setLineWidth(0.5)
#     p.line(50, 65, width - 50, 65)
    
#     # Finalize the PDF and close the canvas
#     p.showPage()
#     p.save()

#     # Move the buffer to the beginning so it can be read later
#     buffer.seek(0)
#     return buffer

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from io import BytesIO
from datetime import date

def generate_pdf(student_name, roll_number, course_name, course_percentage, subject_scores):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    today = date.today
    # Add logo (logo_path is the path to the logo image file)
    logo_path = "static/images/logo.png"
    if logo_path:
        logo = ImageReader(logo_path)
        p.drawImage(logo, 50, height - 100, width=100, height=50, preserveAspectRatio=True, mask='auto')
    
    # Add institute header after the logo
    p.setFont("Helvetica-Bold", 14)
    p.drawString(160, height - 50, "Utkarsh Minds")
    p.setFont("Helvetica", 10)
    p.drawString(160, height - 70, "E-mail: pranav.nerurkar@utkarshminds.com")
    p.drawString(160, height - 85, "Phone: +91 (0) 961-999-7797 | Fax: +91 (0) 456 7891")
    
    # Draw a horizontal line under the header and logo
    p.setLineWidth(0.5)
    p.line(50, height - 100, width - 50, height - 100)
    
    # Add student name and roll number
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 200, f"Student Name: {student_name}")
    p.drawString(100, height - 220, f"Roll Number: {roll_number}")

    # Title: Course information
    p.setFont("Helvetica-Bold", 16)
    p.drawString(100, height - 150, f"Course: {course_name}")
    p.setFont("Helvetica", 12)
    p.drawString(100, height - 170, f"Overall Percentage: {course_percentage}%")
    
    # Table for subjects, scores, and totals
    data = [["Subject", "Score", "Total"]]
    
    # Add subject data to the table (using the extracted report)
    for subject, data_info in subject_scores.items():
        data.append([subject, str(data_info['scores']), str(data_info['totals'])])
    
    # Create table
    table = Table(data, colWidths=[200, 100, 100])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    
    # Place the table on the PDF
    table.wrapOn(p, width, height)
    table.drawOn(p, 100, height - 320)
    
    # # Final grade
    # p.setFont("Helvetica-Bold", 14)
    # p.drawString(100, height - 380, f"Final Grade: {final_grade}")
    
    # Footer
    yr = date.today()
    p.setFont("Helvetica", 10)
    p.drawString(100, 50, "Utkarsh Minds Institute | " + str(yr.year))
    
    # Draw a horizontal line above the footer
    p.setLineWidth(0.5)
    p.line(50, 65, width - 50, 65)
    
    # Finalize the PDF and close the canvas
    p.showPage()
    p.save()

    # Move the buffer to the beginning so it can be read later
    buffer.seek(0)
    return buffer



def send_report_email(request, pdf_buffer, guardian_email):
    # Format the message with the student's name
    message = f'''Dear Parent/Guardian,

This is a final report of your ward of this month.
Please contact us if you have any questions.
Please find the attachment below.

Thank you,
Utkarsh Minds
E-mail: pranav.nerurkar@utkarshminds.com
Phone: +91 (0) 961-999-7797
Fax: +91 (0) 456 7891
'''

        # Create email with attachment
    email = EmailMessage(
            subject='Monthly ScoreCard Report',
            body=message,
            from_email=settings.EMAIL_HOST_USER,
            to=[guardian_email],
        )

        # Attach the generated PDF
    email.attach('report.pdf', pdf_buffer.getvalue(), 'application/pdf')

        # Send the email
    email.send(fail_silently=False)
    
    return render(request, 'quizmgt/emailsent.html')

