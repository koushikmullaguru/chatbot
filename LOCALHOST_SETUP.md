# Localhost Setup Guide

This guide explains how to run the AI School Chat Application on localhost.

## Prerequisites

- Node.js (v16 or higher)
- Python (v3.8 or higher)
- PostgreSQL database
- npm or yarn package manager

## Configuration Changes

The following changes have been made to configure the application for localhost:

### Frontend Configuration

1. **Vite Configuration** (`src/vite.config.ts` and `vite.config.ts`):
   - Added `host: 'localhost'` to ensure the frontend runs on localhost

2. **API Configuration** (`src/api/config.ts`):
   - Created a new API configuration file with base URL set to `http://localhost:8000/api/v1`
   - Defined all API endpoints for the frontend to communicate with the backend

3. **API Service** (`src/api/service.ts`):
   - Created a service class to handle all HTTP requests to the backend
   - Includes token management for authentication

### Backend Configuration

1. **Environment Variables** (`backend/.env`):
   - Added `HOST="localhost"` and `PORT=8000` to specify the backend host and port

2. **CORS Configuration** (`backend/app/core/config.py`):
   - Updated `CORS_ORIGINS` to include `http://localhost:3000`, `http://localhost:5173`, and their 127.0.0.1 equivalents

3. **Startup Script** (`backend/start.py`):
   - Changed the host from `"0.0.0.0"` to `"localhost"` to ensure the backend runs on localhost

## Running the Application

### Option 1: Using the Provided Scripts

#### For Linux/macOS Users:
```bash
chmod +x start-localhost.sh
./start-localhost.sh
```

#### For Windows Users:
```batch
start-localhost.bat
```

These scripts will:
1. Start the backend server on `http://localhost:8000`
2. Start the frontend server on `http://localhost:3000`
3. Display the URLs for both servers and the API documentation

### Option 2: Manual Start

#### Backend:
```bash
cd backend
python start.py
```

#### Frontend:
```bash
npm install
npm run dev
```

## Access Points

Once the servers are running, you can access:

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Troubleshooting

1. **Port Already in Use**:
   - If you get an error that a port is already in use, you can either:
     - Change the port in the respective configuration file
     - Stop the process using the port

2. **CORS Issues**:
   - If you encounter CORS errors, ensure that the frontend URL is included in the `CORS_ORIGINS` list in `backend/app/core/config.py`

3. **Database Connection Issues**:
   - Make sure your PostgreSQL server is running
   - Verify the database connection string in `backend/.env`

4. **Dependencies Issues**:
   - For frontend: Run `npm install` to install all dependencies
   - For backend: Run `pip install -r requirements.txt` to install all Python dependencies

## Development

When making changes to the codebase:

- The backend will automatically reload due to the `reload=True` flag in `backend/start.py`
- The frontend will automatically reload due to Vite's development server

## API Integration

To integrate the frontend with the backend API:

1. Import the API service:
   ```typescript
   import { apiService } from './api/service';
   ```

2. Use the service to make API calls:
   ```typescript
   // Example GET request
   const data = await apiService.get('/endpoint');
   
   // Example POST request
   const response = await apiService.post('/endpoint', { data: 'value' });
   ```

3. Set authentication token after login:
   ```typescript
   apiService.setToken(token);