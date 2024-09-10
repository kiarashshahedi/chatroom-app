/project_root
    ├── app/
    │   ├── main.py            # FastAPI app entry point
    │   ├── auth.py            # JWT authentication and token handling
    │   ├── models.py          # Database models 
    │   ├── database.py        # MongoDB or other database connection setup
    │   ├── routers/
    │   │   ├── chat.py        # Chat-related API routes and WebSocket handling
    │   │   └── media.py       # Media file upload/serve routes
    ├── frontend/
    │   ├── index.html         # Frontend HTML
    │   ├── style.css          # Frontend styles
    │   └── script.js          # Frontend JavaScript
    └── Dockerfile             # Docker configuration for backend