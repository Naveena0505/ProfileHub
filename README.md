# Personal Information System

![image alt](https://github.com/Naveena0505/ProfileHub/blob/0f67c071a0bae1af678c95754d6bf86054829262/ss2.jpeg)

![image alt](https://github.com/Naveena0505/ProfileHub/blob/2082b2b2545c4cacbde974b1a715438eea53eda8/ss1.jpeg)
A simple, web-based application for managing personal records. This system allows users to create, view, update, and delete profiles. It also includes features for photo uploads and exporting data to CSV and PDF formats.

Features
CRUD Operations: Full Create, Read, Update, and Delete functionality for user profiles.

Profile Pictures: Upload, resize, and display a unique photo for each person.

Dynamic Search: A main search on the home page and a live search/filter on the data table.

Data Table View: A comprehensive table on the profile page lists all records, making it easy to browse users.

Data Export: Easily download the current list of users (either full or searched) in both CSV and PDF formats.

User-Friendly Interface: A clean, responsive design built with Bootstrap.

Project Structure
The project is organized into a few key files and folders:

/personal-info-system/
|
|-- app.py                  # The main Flask application with all the logic.
|-- people.db               # The SQLite database file where all data is stored.
|-- requirements.txt        # A list of all Python packages needed.
|
|-- /static/
|   |-- /uploads/           # Directory where user-uploaded photos are saved.
|
|-- /templates/
|   |-- base.html           # The main layout template (navbar, background).
|   |-- index.html          # The home page with the main search bar.
|   |-- profile.html        # The page for viewing/editing a profile and seeing the data table.
|   |-- create_profile.html # The form for adding a new person.

Setup and Installation
Follow these simple steps to get the application running on your local machine.

Prerequisites
You must have Python 3 installed on your computer. You can check this by opening your terminal or command prompt and typing python --version.

Step-by-Step Guide
1. Create a Project Folder
Download or move all the project files (app.py, people.db, etc.) into a single folder on your computer.

2. Open Your Terminal
Navigate into your project folder using the terminal.

# Example for a folder on the Desktop
cd Desktop/personal-info-system

3. Create a Virtual Environment (Recommended)
This creates an isolated space for your project's packages so they don't interfere with other Python projects.

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate

# On Windows
python -m venv venv
.\venv\Scripts\activate

You will know it's active because your terminal prompt will change to show (venv).

4. Install the Required Packages
Use the requirements.txt file to install all the necessary libraries with one command.

pip install -r requirements.txt

5. Run the Application
Once the installation is complete, you can start the Flask server.

python app.py

6. View in Your Browser
You will see output in your terminal telling you the server is running. Open your web browser and go to the following address:
https://www.google.com/search?q=http://127.0.0.1:5000

The application should now be running!

How to Use the System
Home Page: Use the main search bar to find a person by their ID, name, or phone number.

Create a Profile: Click the "Create New Profile" button on the home page to go to a form where you can enter new user details.

View/Edit a Profile: Click on a user from the search results or the data table to go to their profile page. Here, you can edit their details, upload a new photo, and then click "Save All Changes".

Search and Export: On the profile page, use the search bar above the table to filter the records. The "Export CSV" and "Export PDF" buttons will export the data currently visible in the table (so if you've searched for "John", it will only export records matching that search).
