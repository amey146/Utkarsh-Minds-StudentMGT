from django.shortcuts import redirect, render, HttpResponse

from coursemgt.models import Course, Subject

# Create your views here.

def course_home(request):
    courses = Course.objects.all()
    return render(request, "coursemgt/course_home.html", {'courses':courses})

def course_add(request):
    if request.method == 'POST':
        cid = request.POST.get("cid")
        cname = request.POST.get("cname")
        cduration = request.POST.get("cduration")
        c = Course()
        c.c_id = cid
        c.cname = cname
        c.cduration = cduration
        c.save()
        return redirect("/coursemgt")
    return render(request, "coursemgt/course_add.html", {})


def course_update(request, c_id):
    c=Course.objects.get(pk=c_id)
    return render(request, "coursemgt/course_update.html",{'c':c})

def course_delete(request, c_id):
    c=Course.objects.get(pk=c_id)
    c.delete()
    return redirect("/coursemgt")




def subject_add(request):
    if request.method == 'POST':
        sb_id = request.POST.get("sb_id")
        sbname = request.POST.get("sbname")
        course_ids = request.POST.getlist("courses")

        # Check if the subject with the given sb_id already exists
        if Subject.objects.filter(sb_id=sb_id).exists():
            error_message = 'Error! A subject with this ID already exists.'
            courses = Course.objects.all()
            return render(request, "coursemgt/subject_home.html", {'error_message': error_message, 'courses': courses})

        s = Subject(sb_id=sb_id, sbname = sbname)
        s.save()
        for course_id in course_ids:
            course = Course.objects.get(c_id=course_id)
            s.courses.add(course)
        
        return redirect("/coursemgt")
    courses = Course.objects.all()
    return render(request, "coursemgt/subject_add.html", {'courses': courses})


def subject_home(request):
    subjects = Subject.objects.all()
    return render(request,"coursemgt/subject_home.html", {'subjects': subjects})

def subject_delete(request,sb_id):
    s=Subject.objects.get(pk=sb_id)
    s.delete()
    return redirect("/coursemgt/subject_home")

def subject_update(request, sb_id):
    s=Subject.objects.get(pk=sb_id)
    courses = Course.objects.all()
    return render(request, "coursemgt/subject_update.html",{'s':s, 'courses': courses})

def subject_do_update(request, sb_id):
    if request.method == 'POST':
        sb_id = request.POST.get("sb_id")
        sbname = request.POST.get("sbname")
        course_ids = request.POST.getlist("courses")

        s = Subject.objects.get(pk=sb_id)
        s.sbname = sbname
        s.save()

        # Clear existing courses and add the selected ones
        s.courses.clear()
        for course_id in course_ids:
            course = Course.objects.get(c_id=course_id)
            s.courses.add(course)

        return redirect("/coursemgt/subject_home")

    return redirect("/coursemgt/subject_home")

def add_subjectsincourse(request):
    return render(request,"coursemgt/add_subjectsincourse.html")
