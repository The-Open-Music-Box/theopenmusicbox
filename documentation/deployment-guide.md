# TheOpenMusicBox Deployment Guide

This guide explains the complete deployment process for TheOpenMusicBox application, including both backend and frontend components.

## Overview

TheOpenMusicBox is a full-stack application with:
- A **Backend** built with FastAPI and SQLite
- A **Frontend** built with Vue.js and TypeScript

The deployment process involves building both components and deploying them to a Raspberry Pi.

## Directory Structure

```
tomb-rpi/
├── back/                      # Backend code
│   ├── app/                   # FastAPI application
│   │   ├── src/               # Source code
│   │   └── ...
│   ├── export_public_package.sh  # Script to prepare backend for deployment
│   └── ...
├── front/                     # Frontend code
│   ├── src/                   # Vue.js source code
│   ├── dist/                  # Built frontend (after npm run build)
│   └── ...
├── public_release/            # Staging area for deployment
│   └── tomb-rpi/              # Combined backend and frontend
│       ├── app/               # Backend code
│       │   ├── static/        # Frontend static files
│       │   └── ...
│       └── ...
└── sync_to_tmbdev.sh          # Master deployment script
```

## Deployment Process

The deployment process consists of three main steps:

1. Build the frontend
2. Package the backend and include the frontend
3. Synchronize the complete package to the Raspberry Pi

### Step 1: Build the Frontend

The frontend build process compiles the Vue.js application into static files that will be served by the backend.

```bash
cd /path/to/tomb-rpi/front
npm run build
```

This command:
- Compiles and minifies the frontend code
- Creates optimized production assets in the `dist` directory
- Prepares all static assets (JS, CSS, images) for deployment

Build configuration is controlled by:
- `vue.config.js` - Vue CLI configuration
- `.env` files - Environment variables

#### Environment Variables

The frontend relies on several environment variables, most importantly:

- `VUE_APP_API_URL`: The URL where the backend API is accessible
- `VUE_APP_PUBLIC_PATH`: The public path for static assets
- `VUE_APP_ASSETS_DIR`: The directory for assets within the public path

### Step 2: Package the Backend and Include the Frontend

After building the frontend, the backend is prepared for deployment.

```bash
cd /path/to/tomb-rpi/back
./export_public_package.sh
```

This script:
- Creates a clean export of the backend code
- Copies it to the `public_release/tomb-rpi` directory
- Ensures all necessary dependencies are included

The frontend build is then integrated into the backend by copying the contents of the `front/dist` directory to `public_release/tomb-rpi/app/static`.

### Step 3: Synchronize to the Raspberry Pi

The final step is to transfer the complete package to the Raspberry Pi.

```bash
cd /path/to/tomb-rpi
./sync_to_tmbdev.sh
```

This master script:
1. Builds the frontend (calls `npm run build` in the front directory)
2. Exports the backend (calls `export_public_package.sh` in the back directory)
3. Integrates the frontend static files into the backend
4. Uses `rsync` to transfer all files to `/home/admin/tomb/` on the Raspberry Pi
5. Sets proper permissions on the remote files

## Networking Configuration

### Backend Server

The backend server runs on the Raspberry Pi at:
- Host: `localhost` or `theopenmusicbox.local`
- Port: `5004`

### Frontend Access

When deployed, the frontend is served by the backend and can be accessed at:
- URL: `http://theopenmusicbox.local:5004/`

### API and Socket.IO Configuration

The frontend communicates with the backend through:

1. **REST API Calls**: Using Axios to make HTTP requests to endpoints defined in `apiRoutes.ts`
2. **Real-time Events**: Using Socket.IO for WebSocket communication

Critical configuration points:

- The Socket.IO client is configured to connect to the same origin as the web application using `window.location.origin`, which allows it to adapt to different access methods (e.g., localhost, hostname, IP address)
- The API base URL is set by the `VUE_APP_API_URL` environment variable
- During development, API requests are proxied through the Vue dev server as configured in `vue.config.js`

## Troubleshooting

### Connection Issues

If the frontend cannot connect to the backend:

1. Verify that the backend server is running on the Raspberry Pi
2. Check that the Raspberry Pi is accessible at `theopenmusicbox.local`
3. Ensure the backend is listening on port 5004
4. Confirm that the frontend is using the correct API URL
5. Check for CORS issues in the backend logs

### Empty Playlist Display Issues

If playlists are not displayed correctly:

1. Verify the backend API returns the correct format (`{"playlists":[]}` for empty playlists)
2. Check the frontend console for JavaScript errors
3. Ensure the Socket.IO connection is established successfully
4. Validate that the API service correctly handles empty arrays

### Socket.IO Polling Errors

If you see Socket.IO polling errors:

1. Verify network connectivity to the Raspberry Pi
2. Check that Socket.IO is using the same origin as the application
3. Confirm that WebSocket connections are not blocked by any network equipment
4. Try accessing the application using different URLs to identify any hostname resolution issues

## Maintenance

### Updating the Application

To update the application:

1. Make code changes to the frontend or backend
2. Follow the deployment steps above to rebuild and redeploy
3. The `sync_to_tmbdev.sh` script handles the complete deployment process

### Backup

The SQLite database is located at `/home/admin/tomb/app/data/app.db` on the Raspberry Pi. Regular backups of this file are recommended.
