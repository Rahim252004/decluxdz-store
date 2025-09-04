# Overview

DecluxDZ is an Arabic e-commerce platform specializing in gypsum/plaster decorative products for interior design in Algeria. The application serves as an online store where customers can browse products, add items to cart, place orders, and track their order status. It features a complete admin panel for managing products, orders, customers, and categories.

# User Preferences

Preferred communication style: Simple, everyday language.

# System Architecture

## Frontend Architecture
The application uses Flask's Jinja2 templating system with Bootstrap 5 RTL for Arabic language support. The frontend is structured with:
- Base template inheritance pattern for consistent layout
- Responsive design optimized for Arabic RTL reading direction
- JavaScript-based cart functionality with localStorage
- Image gallery and product management interfaces
- Admin dashboard with comprehensive management tools

## Backend Architecture
Built on Flask framework with the following architectural decisions:
- **Modular Route Organization**: Routes are separated into three modules (main routes, admin routes, API routes) for better maintainability
- **Form Handling**: Uses Flask-WTF for form validation and CSRF protection
- **Authentication**: Session-based authentication for admin users with decorator-based access control
- **File Upload Management**: Secure file handling for product images with UUID-based naming

## Database Design
Uses SQLAlchemy ORM with the following core entities:
- **Product**: Bilingual (Arabic/English) product information with category relationships
- **Category**: Product categorization with bilingual naming
- **Order/OrderItem**: Complete order management system with customer details
- **Customer**: Customer information storage for order processing
- **Admin**: Administrative user management with password hashing
- **Contact**: Contact form submissions storage

The database supports both development (SQLite) and production (PostgreSQL via DATABASE_URL) configurations.

## Business Logic
- **Cart Management**: Session-based shopping cart with quantity controls
- **Order Processing**: Complete checkout flow with Algerian province support
- **Inventory Management**: Stock status tracking and featured product designation
- **Order Tracking**: Customer order status tracking system

# External Dependencies

## Core Framework Dependencies
- **Flask**: Web application framework with SQLAlchemy ORM integration
- **Bootstrap 5 RTL**: Frontend framework with right-to-left language support
- **Font Awesome**: Icon library for UI elements

## Regional Localization
- **Algerian Provinces**: Complete list of 58 Algerian wilayas for accurate shipping
- **Arabic Language Support**: RTL layout and Cairo/Tajawal font integration
- **Bilingual Content**: Support for both Arabic and English product information

## File Storage
- **Local File System**: Image upload and storage in uploads directory
- **Static File Serving**: Flask static file serving for product images

## Potential Future Integrations
The architecture supports future integration of:
- Payment gateways for online transactions
- SMS/Email notification services
- Advanced inventory management systems
- Analytics and reporting tools