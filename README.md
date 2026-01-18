# TripGenie

TripGenie is a comprehensive Django-based web application designed to help users plan, manage, and enhance their travel experiences. It includes features for trip planning, budgeting, reviews, membership management, and various travel tools.

## Features

- **Trip Planning**: Create and manage detailed itineraries for your trips.
- **Budget Management**: Track and manage travel expenses with PDF export capabilities.
- **User Reviews**: Add and view reviews for destinations and experiences.
- **Membership System**: User authentication, profiles, and membership tiers.
- **Travel Tools**: Additional utilities to assist with travel planning.
- **Assistant**: AI-powered assistance for trip recommendations.

## Setup

### Prerequisites

- Python 3.8 or higher
- MySQL database (or configure another database in settings.py)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/IqraSayed2/TripGenie.git
   cd TripGenie
   ```

2. **Activate the virtual environment:**
   ```bash
   # On Windows
   TripGenie\env\Scripts\activate

   # On macOS/Linux
   source TripGenie/env/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r TripGenie/tripgenie/requirements.txt
   ```

4. **Configure environment variables:**
   Create a `.env` file in the `TripGenie/tripgenie/` directory with your configuration:
   ```
   SECRET_KEY=your-secret-key
   DEBUG=True
   DATABASE_URL=mysql://user:password@localhost:3306/tripgenie
   # Add other required environment variables (Razorpay keys, Twilio credentials, etc.)
   ```

5. **Run database migrations:**
   ```bash
   cd TripGenie/tripgenie
   python manage.py migrate
   ```

6. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

   Visit `http://127.0.0.1:8000/` in your browser.

### Additional Configuration

- Configure payment gateways (Razorpay) in your environment variables
- Set up email services if needed
- Configure Twilio for SMS services
