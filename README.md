# Flask Clothing Exchange Application

This Flask application is designed for managing and exchanging clothes, including functionalities such as adding, editing, liking, and deleting clothes. It also allows users to request exchanges for items and manage their favorite clothes.

## Features

- User authentication and session management
- Add, edit, and delete clothing items
- Like and unlike items
- View and manage favorite clothing items
- Send and manage exchange requests
- Trend analysis of notes based on various parameters

## Setup and Installation

### Prerequisites

- Python 3.6+
- Flask
- Flask-Login
- Flask-SQLAlchemy
- Werkzeug

### Installing Dependencies

Install all necessary dependencies by running:

pip install flask flask-login flask-sqlalchemy werkzeug

### Running the Application

To start the application, navigate to the application directory and run:

python -m flask run

Ensure that your database and application configurations are set up correctly in your `config.py` or as environment variables.

## Application Structure

- `views.py`: Contains all the routes and views for the application.
- `models.py`: Defines the database models.
- `auth.py`: Manages authentication functionalities.
- `static/`: Contains the CSS and image files.
- `templates/`: Contains the HTML templates for the application views.

### Key Routes

- `/`: The home page showing all liked notes for the current user.
- `/add-item`: Add a new clothing item with detailed attributes and image upload.
- `/like-item/<int:note_id>`: Like or unlike a specific item.
- `/my-favorites`: Display all items liked by the current user.
- `/edit-note/<int:note_id>`: Edit details of a specific item.
- `/all-items`: View all items added by all users.
- `/request-exchange/<int:item_id>`: Request an exchange for an item.
- `/my-requests`: View all exchange requests sent and received.
- `/accept-exchange/<int:request_id>`: Accept an exchange request.
- `/reject-request/<int:request_id>`: Reject an exchange request.
- `/trends`: Analyze trends based on successful exchanges.

## Additional Information

For additional help on configuring and extending this application, you can refer to the Flask [documentation](https://flask.palletsprojects.com/en/2.0.x/).

---
