# HOTEL Booking & Management System (jam_ham)

A Django-based hotel booking and management web application.

---

## 🚀 Quick Setup & Run Instructions

Follow these steps to run the application on your computer after cloning the repository.

### 1. Clone the Repository
```bash
git clone https://github.com/Non7Shox/jam_ham.git
cd jam_ham
```

### 2. Set Up Virtual Environment

**On Windows:**
```powershell
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Database & Load Sample Data
Run migrations to set up the SQLite database locally:
```bash
python manage.py migrate
```

*(Optional)* Load pre-configured sample rooms and room types:
```bash
python manage.py load_sample_data
```

### 5. Create an Admin User (Optional)
To access the admin dashboard:
```bash
python manage.py createsuperuser
```

### 6. Run the Development Server
```bash
python manage.py runserver
```
Open your browser and navigate to: `http://127.0.0.1:8000/`

---

## 📂 Project Structure
- **`accounts/`** - User registration, login, and profiles.
- **`hotels/`** - Room listings, details, and sample data loader.
- **`bookings/`** - Room booking logic and user booking history.
- **`dashboard/`** - Staff/Admin management interface.
- **`config/`** - Main Django project configuration.
