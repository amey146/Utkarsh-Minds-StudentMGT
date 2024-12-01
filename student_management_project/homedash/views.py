from django.shortcuts import render, HttpResponse

from studentmgt.models import Student
import pandas as pd
import io
import base64
from django.shortcuts import render
from django.http import HttpResponse
import os
from django.conf import settings
import matplotlib
matplotlib.use('Agg')  # Use the Agg backend for rendering to files
import matplotlib.pyplot as plt
# Create your views here.

def homedash_home(request):
    return render(request, "homedash/index.html")


def generate_chart(request):
    # Define the directory where CSV files are stored
    csv_directory = os.path.join(settings.MEDIA_ROOT, 'quiz_score')
    
    # Get a list of all CSV files in the directory
    csv_files = [f for f in os.listdir(csv_directory) if f.endswith('.csv')]

    if request.method == 'POST':
        selected_file = request.POST.get('csv_file')
        
        if selected_file:
            # Read the selected CSV file
            csv_file_path = os.path.join(csv_directory, selected_file)
            df = pd.read_csv(csv_file_path)

            # Group by Student Name and Subject to calculate total scores
            score_data = df.groupby('Name')['Score'].sum()

            # Create a bar chart
            fig, ax = plt.subplots()
            score_data.plot(kind='bar', ax=ax)
            ax.set_title('Scores of Students')
            ax.set_xlabel('Student Name')
            ax.set_ylabel('Total Score')

            # Rotate the x-axis labels for better visibility
            ax.tick_params(axis='x', labelrotation=45)

            # Adjust layout to prevent clipping
            plt.tight_layout()

            # Save the chart to a BytesIO object
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)

            # Encode the chart to base64 to send to the template
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()

            return render(request, 'homedash/chart.html', {
                'chart': image_base64,
                'csv_files': csv_files,  # Pass the list of CSV files for the dropdown
            })
    
    return render(request, 'homedash/upload.html', {'csv_files': csv_files})

def visualize_attendance(request):
    # Define the directory where attendance CSV files are stored
    attendance_directory = os.path.join(settings.MEDIA_ROOT, 'attendance')
    
    # Get a list of all CSV files in the directory
    csv_files = [f for f in os.listdir(attendance_directory) if f.endswith('.csv')]

    if request.method == 'POST':
        selected_file = request.POST.get('csv_file')
        
        if selected_file:
            # Read the selected CSV file
            csv_file_path = os.path.join(attendance_directory, selected_file)
            df = pd.read_csv(csv_file_path)

            # Separate student IDs based on status
            present_students = df[df['Status'] == 'P']['Student ID'].tolist()
            absent_students = df[df['Status'] == 'A']['Student ID'].tolist()
            the_class = df['Date'][0]

            # Manually create attendance summary to ensure both Present and Absent are included
            attendance_summary = {
                'Present': len(present_students),
                'Absent': len(absent_students)
            }

            # Create a bar chart for the attendance summary
            fig, ax = plt.subplots()
            ax.bar(attendance_summary.keys(), attendance_summary.values(), color=['green', 'red'])

            # Set chart title and labels
            ax.set_title('Attendance Summary')
            ax.set_xlabel('Attendance Status')
            ax.set_ylabel('Number of Students')

            # Adjust layout to prevent clipping
            plt.tight_layout()

            # Save the chart to a BytesIO object
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)

            # Encode the chart to base64 to send to the template
            image_base64 = base64.b64encode(buf.read()).decode('utf-8')
            plt.close()

            # Pass the chart and the lists of student IDs to the template
            return render(request, 'homedash/chart_att.html', {
                'chart': image_base64,
                'csv_files': csv_files,  # Pass the list of CSV files for the dropdown
                'present_students': present_students,
                'absent_students': absent_students,
                'the_class': the_class
            })

    return render(request, 'homedash/upload_att.html', {'csv_files': csv_files})
