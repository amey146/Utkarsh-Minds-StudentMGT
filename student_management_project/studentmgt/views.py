from django.shortcuts import redirect, render, HttpResponse

from coursemgt.models import Course
from studentmgt.models import Student
from django.contrib import messages

# Create your views here.
def student_home(request):
    std = Student.objects.all()
    return render(request, "studentmgt/student_home.html", {'std': std})



def student_add(request):
    if request.method == 'POST':
        # Retrieve the user inputs
        st_id = request.POST.get("st_id")
        fname = request.POST.get("fname")
        lname = request.POST.get("lname")
        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        st_email = request.POST.get("st_email")
        pr_email = request.POST.get("pr_email")
        phone = request.POST.get("phone")
        pr_phone = request.POST.get("pr_phone")
        address = request.POST.get("address")
        course_ids = request.POST.getlist("courses")
        batch_month = request.POST.get("batch_month")
        batch_year = request.POST.get("batch_year")

        # Check if the student with the given st_id already exists
        if Student.objects.filter(st_id=st_id).exists():
            error_message = 'Error! A student with this Roll ID already exists.'
            courses = Course.objects.all()
            return render(request, "studentmgt/student_add.html", {'error_message': error_message, 'courses': courses})

        # Create and save the student
        s = Student(st_id=st_id, fname=fname, lname=lname, dob=dob, gender=gender,
                    st_email=st_email, pr_email=pr_email, phone=phone, pr_phone=pr_phone ,address=address, batch_mon = batch_month, batch_year = batch_year)
        s.save()

        # Assign selected courses to the student
        for course_id in course_ids:
            course = Course.objects.get(c_id=course_id)
            s.courses.add(course)

        return redirect('/studentmgt')

    courses = Course.objects.all()
    return render(request, "studentmgt/student_add.html", {'courses': courses})



def student_delete(request,st_id):
    s=Student.objects.get(pk=st_id)
    s.delete()
    return redirect("/studentmgt")

def student_update(request, st_id):
    std = Student.objects.get(pk=st_id)
    courses = Course.objects.all()
    return render(request, "studentmgt/student_update.html", {'std': std, 'courses': courses})

def student_do_update(request, st_id):
    if request.method == 'POST':
        st_id = request.POST.get("st_id")
        fname = request.POST.get("fname")
        lname = request.POST.get("lname")
        dob = request.POST.get("dob")
        gender = request.POST.get("gender")
        st_email = request.POST.get("st_email")
        pr_email = request.POST.get("pr_email")
        phone = request.POST.get("phone")
        pr_phone = request.POST.get("pr_phone")
        address = request.POST.get("address")
        course_ids = request.POST.getlist("courses")
        batch_month = request.POST.get("batch_month")
        batch_year = request.POST.get("batch_year")

        std = Student.objects.get(pk=st_id)
        std.fname = fname
        std.lname = lname
        std.dob = dob
        std.gender = gender
        std.st_email = st_email
        std.pr_email = pr_email
        std.phone = phone
        std.pr_phone = pr_phone
        std.address = address
        std.batch_mon = batch_month
        std.batch_year = batch_year
        std.save()

        # Clear existing courses and add the selected ones
        std.courses.clear()
        for course_id in course_ids:
            course = Course.objects.get(c_id=course_id)
            std.courses.add(course)

        return redirect("/studentmgt")

    return redirect("/studentmgt")