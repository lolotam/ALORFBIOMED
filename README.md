# ALORF BIOMED System

Hospital Equipment Maintenance Management System - A comprehensive Flask application for managing PPM (Preventive Maintenance Program), OCM (Operational and Clinical Maintenance) equipment, and training records with mobile-optimized responsive design.

## 🏥 Overview

The ALORF BIOMED System is a professional healthcare equipment management platform designed for biomedical engineering departments in hospitals and medical facilities. It provides comprehensive tracking, maintenance scheduling, and documentation for medical equipment while offering a modern, mobile-first user experience.

## ✨ Key Features

### 📱 Mobile-First Design
- **Responsive Layout**: Fully optimized for mobile devices with CSS Grid and Flexbox
- **Touch-Friendly Navigation**: Hamburger menu with backdrop blur effects
- **Adaptive Tables**: Equipment tables automatically convert to cards on mobile (≤768px)
- **Touch Gestures**: Swipe actions and pull-to-refresh functionality
- **Native Mobile Elements**: iOS/Android optimized date pickers and form inputs
- **Ripple Effects**: Modern button feedback for enhanced user interaction

### 🔧 Equipment Management
- **PPM Equipment**: Preventive maintenance program tracking
- **OCM Equipment**: Operational and clinical maintenance management
- **Equipment History**: Comprehensive maintenance and service records
- **Barcode Generation**: QR codes for easy equipment identification
- **Department Organization**: Equipment categorized by hospital departments

### 👥 User Management & Security
- **Role-Based Access Control**: Admin, Editor, and Viewer roles
- **Permission System**: Granular permissions for different operations
- **Secure Authentication**: Password hashing and session management
- **Audit Logging**: Complete activity tracking for compliance

### 📊 Dashboard & Analytics
- **Overview Dashboard**: Equipment status and maintenance summaries
- **Responsive Cards**: Mobile-optimized dashboard layout
- **Timeline View**: Maintenance history visualization
- **Quick Actions**: Fast access to common tasks

### 📋 Training Management
- **Staff Training Records**: Track training certifications and renewals
- **Training History**: Comprehensive staff development tracking
- **Certification Management**: Monitor training compliance

### 🔄 Data Management
- **Import/Export**: CSV templates for bulk data operations
- **Automatic Backups**: Scheduled system backups
- **Data Validation**: Comprehensive input validation and sanitization
- **Email Notifications**: Automated maintenance reminders

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/lolotam/ALORFBIOMED.git
   cd ALORFBIOMED
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python create_tables.py
   python populate_initial_data.py
   ```

5. **Create admin user**
   ```bash
   python create_admin.py
   ```

6. **Run the application**
   ```bash
   python -m flask --app app.main run --debug --port 5001
   ```

7. **Access the application**
   - Open your browser and navigate to `http://localhost:5001`
   - Login with your admin credentials

## 📱 Mobile Features

### Responsive Design
- **Breakpoints**: Optimized for mobile (≤768px), tablet (769px-1024px), and desktop (>1024px)
- **Touch Targets**: Minimum 44px touch targets for accessibility
- **Viewport Optimization**: Prevents zoom on input focus for iOS devices

### Mobile Navigation
- **Hamburger Menu**: Collapsible navigation with smooth animations
- **Backdrop Blur**: Modern iOS-style backdrop effects
- **Touch-Friendly**: Large touch areas and intuitive gestures

### Equipment Lists
- **Card Conversion**: Tables automatically become cards on mobile
- **Swipe Actions**: Touch gestures for equipment operations
- **Pull-to-Refresh**: Native mobile refresh experience

### Forms & Inputs
- **Mobile Keyboards**: Optimized input types for mobile keyboards
- **Date Pickers**: Native date/time pickers for mobile devices
- **Form Validation**: Real-time validation with mobile-friendly messages

## 🏗️ Technology Stack

### Backend
- **Flask**: Python web framework
- **SQLite**: Lightweight database for development
- **Werkzeug**: WSGI utilities and security
- **APScheduler**: Background task scheduling
- **Mailjet**: Email service integration

### Frontend
- **Bootstrap 5**: Responsive CSS framework
- **Vanilla JavaScript**: Mobile enhancement scripts
- **CSS Grid & Flexbox**: Modern layout techniques
- **Progressive Enhancement**: Works without JavaScript

### Mobile Enhancements
- **Touch Events**: Native touch gesture support
- **Intersection Observer**: Performance-optimized scroll detection
- **CSS Variables**: Dynamic theming and responsive design
- **Modern CSS**: backdrop-filter, grid, flexbox, and animations

## 📁 Project Structure

```
ALORFBIOMED/
├── app/
│   ├── models/          # Data models
│   ├── routes/          # URL routes and views
│   ├── services/        # Business logic
│   ├── static/          # CSS, JS, and assets
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   └── mobile.css    # Mobile optimizations
│   │   └── js/
│   │       ├── main.js
│   │       └── mobile.js     # Mobile enhancements
│   ├── templates/       # Jinja2 templates
│   └── utils/          # Utility functions
├── data/               # Application data
├── migrations/         # Database migrations
└── tests/             # Test suite
```

## 🛡️ Security Features

- **Input Validation**: Comprehensive sanitization of all user inputs
- **Password Hashing**: Secure bcrypt password hashing
- **Session Management**: Secure session handling
- **CSRF Protection**: Cross-site request forgery prevention
- **Audit Logging**: Complete activity audit trail

## 📧 Email Configuration

The system supports automated email notifications:

1. Configure email settings in the admin panel
2. Set up Mailjet API credentials
3. Enable automatic maintenance reminders
4. Customize notification schedules

## 🔧 Configuration

### Environment Variables
Create a `.env` file with:
```
FLASK_ENV=development
SECRET_KEY=your-secret-key
MAILJET_API_KEY=your-mailjet-api-key
MAILJET_SECRET_KEY=your-mailjet-secret-key
```

### Application Settings
- Configure through the web interface admin panel
- Backup and restore settings
- Email notification preferences
- Maintenance reminder schedules

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

## 📚 API Documentation

The application provides REST API endpoints for:
- Equipment management
- Training records
- User management
- Audit logs

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🏥 About ALORF BIOMED

Developed for healthcare facilities to streamline biomedical equipment management, ensuring compliance with medical device regulations and maintenance standards.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation wiki

---

**Built with ❤️ for healthcare professionals**


