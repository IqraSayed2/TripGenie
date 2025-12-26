# TripGenie

TripGenie is a comprehensive Django-based web application designed to help users plan, manage, and enhance their travel experiences. It includes features for trip planning, budgeting, reviews, membership management, and various travel tools.

## Features

- **Trip Planning**: Create and manage detailed itineraries for your trips.
- **Budget Management**: Track and manage travel expenses with PDF export capabilities.
- **User Reviews**: Add and view reviews for destinations and experiences.
- **Membership System**: User authentication, profiles, and membership tiers.
- **Travel Tools**: Additional utilities to assist with travel planning.
- **Assistant**: AI-powered assistance for trip recommendations.

## Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/TripGenie.git
   cd TripGenie
   ```

2. **Set up a virtual environment**:

   ```bash
   python -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:

   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (optional):

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**:

   ```bash
   python manage.py runserver
   ```

   Visit `http://127.0.0.1:8000/` in your browser.

## Usage

- Access the application through your web browser.
- Register an account or log in to start planning trips.
- Use the various apps (trips, budget, review, etc.) to manage your travel data.

## Deployment

This project can be deployed on platforms like PythonAnywhere, Heroku, or AWS. Ensure to set environment variables for sensitive data (e.g., SECRET_KEY, database credentials).

For PythonAnywhere:

- Clone the repo.
- Set the source directory to the project root.
- Configure the WSGI file to point to `tripgenie.wsgi:application`.

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature-name`.
3. Commit changes: `git commit -am 'Add feature'`.
4. Push to the branch: `git push origin feature-name`.
5. Submit a pull request.

## Contact

For questions or support, please open an issue on GitHub.
