# E-Community Website

A web-based community management system for **Barangay Tacdangan**, designed to make community services and resident requests easier to access and manage.

## Overview

E-Community provides a website where residents can access community information and submit requests, while administrators can manage submissions through an admin interface.

## Features

### Resident Features
- Resident registration and sign-in
- Community information and services pages
- Health-related requests
- Assistance requests
- Complaint submission
- Document requests and request tracking
- Contact and messaging functionality

### Admin Features
- Admin dashboard
- Resident management
- Document request management
- Health request management
- Assistance request management
- Complaint management
- Message management

## Technologies Used

- **Programming Language:** Python
- **Framework:** Flask
- **Database:** MySQL
- **Frontend:** HTML and CSS
- **Database Connector:** MySQL Connector/Python
- **Environment Configuration:** python-dotenv
- **Development Tool:** Visual Studio Code

## Project Structure

```text
E-Community/
├── app.py
├── requirements.txt
├── .gitignore
├── static/
│   ├── css/
│   └── images/
└── templates/
    ├── index.html
    ├── about.html
    ├── service.html
    ├── signin.html
    ├── register.html
    ├── req-doc.html
    ├── track.html
    └── ... other page templates
```

## Getting Started

### Prerequisites

- Python installed
- MySQL Server installed and running
- A configured `e_community` database with the required tables

**Note:** The database schema and resident records are not included in this repository.

### 1. Clone the Repository

```bash
git clone https://github.com/HanGo21-afk/E-Community-.git
cd E-Community-
```

### 2. Install Dependencies

It is recommended to create and activate a Python virtual environment first.

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install the required packages:

```bash
python -m pip install -r requirements.txt
```

### 3. Configure Environment Variables

Create a `.env` file in the project root. Do not upload this file to GitHub.

Add your local configuration using your own MySQL credentials:

```dotenv
FLASK_SECRET_KEY=replace-with-a-long-random-secret
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your-local-mysql-password
DB_NAME=e_community
```

Replace the example values with your own settings. Ensure your MySQL database and required tables are already configured.

### 4. Run the Application

```bash
python app.py
```

Open the local address shown in the terminal, usually:

```text
http://127.0.0.1:5000
```

## Security Notes

- Keep `.env` and all passwords out of version control.
- Never publish real resident information or private records.
- Use a unique, securely generated Flask secret key.
- The Flask development server is intended for local development, not public production deployment.

## Project Purpose

This project demonstrates the development of a community management website using Flask, MySQL, HTML, and CSS. It is intended as a learning and portfolio project.
