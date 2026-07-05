
# AI-Powered FYP Recommender System

An intelligent web application that recommends personalized Final Year Projects (FYPs) to Computer Science students using Machine Learning.

## Project Overview

This system helps students choose suitable FYPs based on their skills, interests, experience level, available time, and hardware resources. The recommendation engine uses a Random Forest model to rank projects and suggest the best matches.

## Features

Student registration and profile creation

AI-powered FYP recommendations

Skill-based project matching

Interest-based filtering

Learning path generation for missing skills

Admin dashboard for managing projects and skills

Supervisor-approved project highlighting

Offline-first operation (no external API dependency)

## Tech Stack

Frontend

HTML5

CSS3

JavaScript (ES6)

Bootstrap 5

Backend

Python

Django

Machine Learning

Scikit-learn

Random Forest Classifier

Pandas

NumPy

Database

SQLite

## System Architecture

The application follows a layered architecture:

Presentation Layer – HTML, CSS, JavaScript, Bootstrap

Application Layer – Django Views & Routing

Business Logic Layer – Recommendation & Learning Path Logic

AI Layer – Random Forest Model

Data Layer – SQLite Database

## Installation

1. Clone the repository

git clone https://github.com/your-username/AI-Project-Recommendation-System.git

2. Navigate to the project folder

cd AI-Project-Recommendation-System

3. Install dependencies

pip install -r requirements.txt

4. Run migrations

python manage.py migrate

5. Start the development server

python manage.py runserver

6. Open in browser

http://127.0.0.1:8000/

## Project Structure

AI-Project-Recommendation-System/

├── manage.py

├── requirements.txt

├── README.md

├── templates/

├── static/

├── media/

├── app/

└── database/

## Future Improvements

NLP-based project matching

AI chatbot for project guidance

Mobile application

Real-time analytics dashboard

Peer reviews and project ratings

## Team

Abdullah Khan – AI/ML Lead & Backend Developer

Sardar Muhammad Umar – Frontend Lead & UI/UX Designer

Awais Ahmed – Data Engineer & Testing Lead

## License

This project is developed for educational and research purposes.
