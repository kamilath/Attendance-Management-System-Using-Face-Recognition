from flask import Flask, request, render_template, redirect, url_for, session, flash
import os
import numpy as np
import pandas as pd
import csv
import cv2
from deepface import DeepFace
import pywhatkit as kit
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.urandom(16)  # Random secret key for session management

# Directory for uploaded images
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Load student data from CSV file
def load_students_data(csv_file):
    students_data = []
    with open(csv_file, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if os.path.exists(row['image_path']):  # Check if image exists
                students_data.append({
                    'regno': row['regno'],
                    'name': row['name'],
                    'image_path': row['image_path']
                })
    return students_data

# Detect and align faces in the classroom image
def detect_and_align_faces(image_path):
    # Use OpenCV's face detector (Haar Cascade) to detect faces
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    image = cv2.imread(image_path)
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5)

    aligned_faces = []
    for (x, y, w, h) in faces:
        face = image[y:y+h, x:x+w]  # Crop the face from the image
        aligned_face = cv2.resize(face, (224, 224))  # Resize the face to the input size for DeepFace models
        aligned_faces.append(aligned_face)
    
    return aligned_faces

# Recognize faces in the classroom image using DeepFace
def recognize_faces_deepface(class_image_path, students_data):
    present_students = []
    absent_students = [student['regno'] for student in students_data]
    unknown_faces = 0
    
    # Detect and align faces in the classroom image
    aligned_faces = detect_and_align_faces(class_image_path)
    
    if not aligned_faces:
        print("No faces detected in the classroom image.")
        return present_students, absent_students, unknown_faces

    # Loop through each detected face in the classroom image
    for detected_face in aligned_faces:
        temp_face_path = 'temp_detected_face.jpg'
        cv2.imwrite(temp_face_path, detected_face)

        matched = False
        # Loop through the student data and compare each student image with the detected face
        for student in students_data:
            try:
                # Use multiple models for verification
                result_vgg = DeepFace.verify(
                    img1_path=temp_face_path, 
                    img2_path=student['image_path'], 
                    model_name='VGG-Face',
                    enforce_detection=False
                )

                result_facenet = DeepFace.verify(
                    img1_path=temp_face_path, 
                    img2_path=student['image_path'], 
                    model_name='Facenet',
                    enforce_detection=False
                )

                # If either model verifies the face, mark the student as present
                if result_vgg["verified"] or result_facenet["verified"]:
                    if student['regno'] not in present_students:
                        present_students.append(student['regno'])
                        absent_students.remove(student['regno'])
                    matched = True
                    break
            except Exception as e:
                print(f"Error processing {student['name']}: {e}")
        
        if not matched:
            unknown_faces += 1
    
    return present_students, absent_students, unknown_faces

# Write present and absent students to separate CSV files
def write_attendance_to_csv(present_students, absent_students, output_present_csv, output_absent_csv):
    # Write present students
    with open(output_present_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['regno', 'status'])  # Header
        for regno in present_students:
            writer.writerow([regno, 'Present'])
    
    # Write absent students
    with open(output_absent_csv, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['regno', 'status'])  # Header
        for regno in absent_students:
            writer.writerow([regno, 'Absent'])

# Function to create a summary message with attendance details
def create_attendance_summary(present_students, absent_students, unknown_faces):
    present_str = ', '.join(present_students) if present_students else "None"
    absent_str = ', '.join(absent_students) if absent_students else "None"
    
    summary = f"""
    Attendance Report:
    
    Present Students:
    {present_str}
    
    Absent Students:
    {absent_str}
    
    Unknown Faces Detected: {unknown_faces}
    """
    
    return summary

# Function to send WhatsApp message with the attendance summary
def send_whatsapp_message(phone_number, message):
    try:
        # Get current time and add 1 minute to send message
        current_time = datetime.now()
        future_time = current_time + timedelta(minutes=1)
        hours = future_time.hour
        minutes = future_time.minute

        # Send message
        kit.sendwhatmsg(phone_number, message, hours, minutes)
        print("Message sent successfully!")
    except Exception as e:
        print(f"Error sending message: {e}")

# Flask routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Simple authentication
        if username == 'admin' and password == 'admin_pass':  # Replace with your admin credentials
            session['user_type'] = 'admin'
            return redirect(url_for('attendance'))
        elif username == 'staff' and password == 'staff_passs':  # Replace with your staff credentials
            session['user_type'] = 'staff'
            return redirect(url_for('upload_file'))
        else:
            flash('Invalid credentials', 'danger')

    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if session.get('user_type') != 'staff':
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filepath)

            # Load student data
            students_csv = 'students.csv'  # Path to students CSV file
            students_data = load_students_data(students_csv)

            # Recognize faces and get attendance
            present_students, absentees, unknown_faces = recognize_faces_deepface(filepath, students_data)

            # Update attendance records (for present and absent students)
            write_attendance_to_csv(present_students, absentees, 'present_students.csv', 'absent_students.csv')

            # Create attendance summary
            summary_message = create_attendance_summary(present_students, absentees, unknown_faces)

            # Send WhatsApp message with the summary
            phone_number = '+918056367687'  # Ensure the phone number is in international format
            send_whatsapp_message(phone_number, summary_message)

            return render_template('results.html', present_students=present_students, absentees=absentees)

    return render_template('upload.html')

@app.route('/attendance')
def attendance():
    if session.get('user_type') != 'admin':
        return redirect(url_for('login'))

    # Load attendance records
    attendance_data = pd.read_csv('attendance.csv')
    return render_template('attendance.html', attendance_data=attendance_data)

@app.route('/logout')
def logout():
    session.pop('user_type', None)
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
