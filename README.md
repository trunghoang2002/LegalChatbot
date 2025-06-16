# Legal Chatbot

A full-stack legal chatbot application that provides legal information and assistance through an interactive chat interface.

## Project Overview

This project consists of a modern web application with a React frontend and Python backend, utilizing various technologies for natural language processing and vector storage.

## Architecture

The application is built using a microservices architecture with the following components:

- **Frontend**: React-based web application served through Nginx
- **Backend**: Python FastAPI server
- **Database**: PostgreSQL for persistent storage
- **Vector Database**: Qdrant for semantic search and embeddings
- **Containerization**: Docker and Docker Compose for easy deployment

## Prerequisites

- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.10+ (for local backend development)

## Getting Started

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone <repository-url>
cd LegalChatbot
```

2. Create a `.env` file in the backend directory with your configuration:
```bash
cp backend/.env.example backend/.env
# Edit the .env file with your settings
```

3. Start the application using Docker Compose:
```bash
docker-compose up --build
```

The application will be available at:
- Frontend: http://localhost:80
- Backend API: http://localhost:5000
- API Documentation: http://localhost:5000/api/docs

### Local Development

#### Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm start
```

#### Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start the backend server:
```bash
python wsgi.py
```

## Project Structure

```
LegalChatbot/
├── frontend/                    # React frontend application
│   ├── src/                    # Source code
│   │   ├── components/        # React components
│   │   ├── pages/            # Page components
│   │   ├── services/         # API services
│   │   ├── utils/            # Utility functions
│   │   ├── styles/           # CSS/SCSS files
│   │   └── App.js            # Main application component
│   ├── public/                # Static files
│   │   ├── index.html        # HTML template
│   │   └── assets/           # Images, fonts, etc.
│   ├── nginx.conf            # Nginx configuration for production
│   ├── Dockerfile            # Frontend container configuration
│   ├── Dockerfile_without_nginx  # Alternative Dockerfile for development
│   ├── package.json          # Node.js dependencies and scripts
│   └── .gitignore           # Git ignore rules
│
├── backend/                    # Python backend application
│   ├── pythonllm/            # LLM integration
│   │   ├── models/          # LLM model implementations
│   │   └── utils/           # LLM utility functions
│   ├── embedding/            # Embedding models
│   │   ├── models/          # Embedding model implementations
│   │   └── utils/           # Embedding utilities
│   ├── dataset/             # Training data
│   │   ├── raw/            # Raw training data
│   │   └── processed/      # Processed training data
│   ├── migrations/          # Database migrations
│   ├── server_stream.py     # Main FastAPI application with streaming support
│   ├── models.py           # Database models
│   ├── migrations.py       # Migration utilities
│   ├── wsgi.py            # WSGI entry point
│   ├── gunicorn_config.py # Gunicorn configuration
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile         # Backend container configuration
│   └── .env              # Environment variables
│
└── docker-compose.yaml        # Container orchestration
```

## Detailed Component Description

### Frontend Components

#### Configuration Files
- `nginx.conf`: Nginx configuration for serving the React application in production
- `Dockerfile`: Production Docker configuration using Nginx
- `Dockerfile_without_nginx`: Development Docker configuration without Nginx
- `package.json`: Node.js project configuration and dependencies

#### Source Code Structure
- `src/components/`: Reusable React components
- `src/pages/`: Page-level components
- `src/services/`: API integration and service layer
- `src/utils/`: Helper functions and utilities
- `src/styles/`: CSS/SCSS styling files

### Backend Components

#### Core Application Files
- `server_stream.py`: Main FastAPI application with streaming support for real-time chat
- `models.py`: SQLAlchemy database models
- `wsgi.py`: WSGI entry point for production deployment
- `gunicorn_config.py`: Gunicorn server configuration

#### LLM Integration
- `pythonllm/`: Language model integration
  - Models for different LLM providers
  - Utility functions for text processing
  - Response generation logic

#### Embedding System
- `embedding/`: Vector embedding system
  - Model implementations for text embeddings
  - Utilities for vector operations
  - Integration with Qdrant vector database

#### Data Management
- `dataset/`: Training and reference data
  - Raw legal documents and training data
  - Processed and indexed data
  - Data preprocessing scripts

#### Database
- `migrations/`: Database migration files
- `migrations.py`: Migration utilities and scripts

### Docker Configuration
- `docker-compose.yaml`: Orchestrates all services:
  - Frontend container with Nginx
  - Backend FastAPI container
  - PostgreSQL database
  - Qdrant vector database
  - Network configuration
  - Volume management

## Features

- Interactive chat interface with real-time streaming responses
- Legal information retrieval using semantic search
- Vector-based document storage and retrieval
- RESTful API endpoints with OpenAPI documentation
- Containerized deployment for easy scaling
- Database migrations for schema management
- Environment-based configuration

## API Documentation

The API documentation is available at `http://localhost:5000/api/docs` when running the backend server. It provides detailed information about all available endpoints and their usage.

## Contact

For any questions or concerns, please open an issue in the repository. 