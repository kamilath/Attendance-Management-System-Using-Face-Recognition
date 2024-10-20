# Attendance-Management-System-Using-Face-Recognition
This project implements a web-based attendance management system that utilizes face recognition technology to mark student attendance. The system allows staff to upload classroom images, processes the images to recognize faces, and sends attendance summaries via WhatsApp.
## Technologies Used
- Python
- Flask
- OpenCV
- DeepFace
- Pandas
- PyWhatKit
- HTML/CSS (for frontend)
## Prerequisites
- Python 3.x
- pip (Python package installer)
## Run the application:
1.python app.py

2.Access the application: Open your web browser and go to http://127.0.0.1:5000/.
## Usage
**1.Login**:
- Login as 'admin' or 'staff' using the credentials:
- Admin credentials: username: admin, password: admin_pass
- Staff credentials: username: staff, password: staff_pass
  
**2.Upload Classroom Image**:
- Navigate to the upload page after logging in as staff.
- Upload the classroom image containing students' faces.
  
**3.View Attendance**:Admin can view attendance records from the attendance page.

**4WhatsApp Notification**:After processing the image, an attendance summary will be sent to the specified WhatsApp number.
## Functionality
**1.Face Detection and Recognition**: The system uses OpenCV to detect and align faces in the uploaded classroom image. It utilizes the DeepFace library to verify detected faces against the registered student images.
  
**2.Attendance Management**: The system marks students as present or absent based on the recognized faces and generates an attendance summary.

**3.WhatsApp Notification**: The attendance summary is sent to a specified phone number using PyWhatKit.

## Results
Upon successful processing, the application displays:
- List of present students
- List of absent students
- Count of unknown faces detected
An attendance summary is also sent to the configured WhatsApp number.
