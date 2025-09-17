# Identity Documents Feature

This document describes the identity documents feature that has been added to the HRMS system.

## Overview

The identity documents feature allows users to upload and manage their identity verification documents including:
- Profile Image (JPG, PNG)
- Aadhaar Card Front (JPG, PNG, PDF)
- Aadhaar Card Back (JPG, PNG, PDF)
- PAN Card (JPG, PNG, PDF)

## Backend Changes

### Database Schema
New columns added to the `users` table:
- `profile_image` (VARCHAR) - Path to profile image file
- `aadhaar_front` (VARCHAR) - Path to Aadhaar front image file
- `aadhaar_back` (VARCHAR) - Path to Aadhaar back image file
- `pan_image` (VARCHAR) - Path to PAN image file

### API Endpoints
New endpoints added to `/users` router:
- `POST /users/upload-profile-image` - Upload profile image
- `POST /users/upload-aadhaar-front` - Upload Aadhaar front
- `POST /users/upload-aadhaar-back` - Upload Aadhaar back
- `POST /users/upload-pan` - Upload PAN card

### File Storage
- Files are stored in the `uploads/` directory
- Static file serving is configured at `/uploads` endpoint
- File naming convention: `{user_id}_{document_type}_{uuid}.{extension}`
- Maximum file size: 10MB
- Supported formats: JPG, JPEG, PNG, PDF

### Security Features
- File type validation
- File size validation
- Unique filename generation to prevent conflicts
- User authentication required for all uploads

## Frontend Changes

### Components
- **FileUpload.tsx** - Reusable file upload component with drag-and-drop support
- **Profile.tsx** - Updated to include identity document upload sections
- **UserManagement.tsx** - Updated to display identity documents in admin panel

### Features
- Drag-and-drop file upload
- File preview for images
- Progress indicators during upload
- File validation (type and size)
- Document viewing links
- Responsive design

## Installation & Setup

### 1. Run Database Migration
```bash
cd Backend
python migrate_identity_documents.py
```

### 2. Create Uploads Directory
```bash
mkdir uploads
```

### 3. Update Dependencies
The following Python packages are required (already in requirements.txt):
- `python-multipart` - For file upload handling

### 4. Frontend Dependencies
No additional dependencies required for the frontend.

## Usage

### For Users
1. Navigate to Profile page
2. Scroll to "Identity Documents" section
3. Upload required documents using drag-and-drop or click to browse
4. View uploaded documents using the "View" links

### For Admins
1. Navigate to User Management page
2. View uploaded documents for each user in the user list
3. Click on document links to view files

## File Structure
```
Backend/
├── uploads/                    # File storage directory
├── migrate_identity_documents.py  # Database migration script
└── app/
    ├── models.py              # Updated User model
    ├── schema.py              # Updated schemas
    ├── routes/users.py        # File upload endpoints
    └── main.py                # Static file serving

Frontend/src/
├── components/
│   └── FileUpload.tsx         # File upload component
├── pages/
│   ├── Profile.tsx            # Updated profile page
│   └── admin/
│       └── UserManagement.tsx # Updated admin panel
└── api/
    └── services.ts            # File upload API calls
```

## API Examples

### Upload Profile Image
```javascript
const formData = new FormData();
formData.append('file', file);
const response = await userService.uploadProfileImage(file);
```

### Get User Profile (includes document paths)
```javascript
const response = await userService.getProfile();
// response.data.profile_image, aadhaar_front, etc.
```

## Error Handling
- File type validation errors
- File size limit exceeded
- Upload failures with user-friendly messages
- Network error handling

## Security Considerations
- Files are validated before saving
- User authentication required
- File paths are stored, not file contents
- Static file serving with proper headers

## Future Enhancements
- Document verification status tracking
- Document expiration dates
- Bulk document upload
- Document approval workflow
- Image compression and optimization
