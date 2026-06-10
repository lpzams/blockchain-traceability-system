# Blockchain Product Traceability System

A blockchain-based product traceability management system built with Flask, supporting multi-role collaboration and advanced features.

## 🚀 Quick Start

### 1. Initialize Database
```bash
python scripts/init_db.py
```
Enter `y` when prompted to create demo data.

### 2. Start Application
```bash
python app.py
```

### 3. Access System
Open your browser and visit: `http://localhost:5000`

## 👤 Demo Accounts

| Username | Password | Role |
|----------|----------|------|
| admin | 1 | Administrator |
| manufacturer1 | 123456 | Manufacturer |
| distributor1 | 123456 | Distributor |
| consumer1 | 123456 | Consumer |
| regulator1 | 123456 | Regulator |

## 🎯 Core Features

### Basic Features
- ✅ User Management (Multi-role permissions)
- ✅ Product Registration & Management
- ✅ Ownership Transfer
- ✅ Quality Inspection Records
- ✅ Logistics Tracking
- ✅ Blockchain Explorer
- ✅ Product Traceability Query

### Advanced Features (Navigation Bar - Advanced Features)
1. **Product Certification** - Tamper-proof certificates with SHA256 encryption
2. **Anti-Counterfeit Verification** - Multi-layer hash encryption + QR code verification
3. **Chain Integrity Verification** - Automatic detection of traceability chain continuity
4. **Batch Management Analytics** - Batch quality statistics and risk assessment
5. **Smart Contracts** - Automated supply chain transaction rules

## 📦 Sample Batch Numbers

Available batch numbers in demo data:
- `001` - West Lake Longjing Tea
- `002` - Organic Green Tea
- `003` - Tieguanyin Tea
- `004` - Organic Rice
- `005` - Black Sesame

## 📁 Project Structure

```
blockchain-traceability-system/
├── app.py                 # Application entry point
├── config/               # Configuration files
├── models/               # Data models
│   ├── database.py       # Database operations
│   ├── blockchain.py     # Blockchain core
│   └── blockchain_features.py  # Advanced features
├── routes/               # Routes
│   ├── auth.py          # Authentication
│   ├── manufacturer.py  # Manufacturer
│   ├── distributor.py   # Distributor
│   ├── consumer.py      # Consumer
│   ├── admin.py         # Administrator
│   ├── regulator.py     # Regulator
│   └── blockchain_features.py  # Advanced features
├── templates/            # HTML templates
├── static/              # Static resources
├── services/            # Business services
├── scripts/             # Utility scripts
│   └── init_db.py       # Database initialization
└── data/                # Data storage
    └── blockchain.db    # SQLite database
```

## 🔧 Tech Stack

- **Backend**: Python 3.9+, Flask
- **Database**: SQLite
- **Frontend**: Bootstrap 5, jQuery
- **Blockchain**: Custom PoW blockchain implementation
- **Encryption**: SHA256, MD5, hashlib

## 📝 Usage Instructions

### Add New User
After running the application, log in with the administrator account and add new users in the admin panel.

### Register Product
Log in with a manufacturer account and fill in product information on the "Register Product" page.

### Transfer Ownership
Select a product from the product list and click "Transfer Ownership".

### View Traceability
Consumer accounts can view complete product traceability information after logging in.

## 🎨 Advanced Features Usage

1. Log in to the system
2. Click **👑 Advanced Features** in the navigation bar
3. Enter product ID or batch number on the feature cards
4. View the corresponding feature page

**Examples**:
- Product Certification: Enter `001`
- Anti-Counterfeit Verification: Enter `002`
- Chain Integrity Verification: Enter `003`
- Batch Management: Enter `001`

## 📄 License

This project is for educational and demonstration purposes only.

---

**Development Year**: 2026

## 🌐 Language

- [中文文档](README.md)
- [English Documentation](README_EN.md)
