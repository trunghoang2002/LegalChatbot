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
├── frontend/                                           # React frontend application
│   ├── src/                                            # Source code
│   │   ├── components/                                 # React components
│   │   │   ├── Chat/                                   # Chat-related components
│   │   │   │   ├── Chat.js                             # Main chat component
│   │   │   │   ├── Chat.css                            # Chat styles
│   │   │   │   ├── ChatMessage.js                      # Individual message component
│   │   │   │   ├── ChatSession.js                      # Chat session component
│   │   │   │   ├── NewSessionModal.js                  # New session modal
│   │   │   │   ├── RenameSessionModal.js               # Rename session modal
│   │   │   │   ├── ChatSourcesModal.js                 # Chat sources modal
│   │   │   │   └── DeleteSessionModal.js               # Delete session modal
│   │   │   ├── SignIn.js                               # Sign in component
│   │   │   ├── SignUp.js                               # Sign up component
│   │   │   ├── SignUp.module.css                       # Sign up styles
│   │   │   ├── validate.js                             # Form validation utilities
│   │   │   └── toast.js                                # Toast notification component
│   │   ├── img/                                        # Image assets
│   │   ├── App.js                                      # Main application component
│   │   ├── App.test.js                                 # App component tests
│   │   ├── config.js                                   # Application configuration
│   │   ├── index.js                                    # Application entry point
│   │   ├── index.css                                   # Global styles
│   │   ├── normalize.css                               # CSS reset
│   │   ├── reportWebVitals.js                          # Performance monitoring
│   │   └── setupTests.js                               # Test configuration
│   ├── public/                                         # Static files
│   │   └── index.html                                  # HTML template
│   ├── nginx.conf                                      # Nginx configuration for production
│   ├── Dockerfile                                      # Frontend container configuration
│   ├── package.json                                    # Node.js dependencies and scripts
│   └── .gitignore                                      # Git ignore rules
│
├── backend/                                            # Python backend application
│   ├── pythonllm/                                      # LLM integration and processing
│   │   ├── handle_llm.py                               # LLM model handling and response generation
│   │   ├── handle_qdrant.py                            # Qdrant vector database operations
│   │   ├── handle_graph.py                             # Agent operations
│   │   └── handle_retriever.py                         # Document retrieval logic
│   ├── embedding/                                      # Embedding models and data
│   │   ├── output_v1/                                  # Version 1 embedding outputs
│   │   ├── output_v2/                                  # Version 2 embedding outputs
│   │   ├── corpus_embeddings_v1.pt                     # Version 1 corpus embeddings
│   │   └── corpus_embeddings_v2.pt                     # Version 2 corpus embeddings
│   ├── data/                                           # Training and reference data
│   │   ├── all_docs.json                               # Document collection
│   │   └── all_doc_metas.json                          # Document metadata
│   ├── migrations/                                     # Database migrations
│   ├── main.py                                         # Main Flask application
│   ├── swagger.json                                    # OpenAPI/Swagger documentation
│   ├── models.py                                       # Database models
│   ├── migrations.py                                   # Migration utilities
│   ├── wsgi.py                                         # WSGI entry point
│   ├── gunicorn_config.py                              # Gunicorn server configuration
│   ├── requirements.txt                                # Python dependencies
│   ├── Dockerfile                                      # Backend container configuration
│   └── __init__.py                                     # Package initialization
│
├── dataset/                                            # Dataset and data processing
│   ├── raw_data/                                       # Raw legal documents
│   │   ├── LuatDanSu/                                  # Civil Law documents
│   │   ├── HienPhap/                                   # Constitution documents
│   │   ├── LuatHinhSu/                                 # Criminal Law documents
│   │   ├── LuatLaoDong/                                # Labor Law documents
│   │   └── legal-conversation-v2.zip                   # Legal conversation dataset
│   ├── processed_data/                                 # Processed and structured data
│   │   ├── Evaluation Data/
│   │   │   ├── eval_corpus.json                        # Evaluation corpus
│   │   │   ├── eval_questions.json                     # Evaluation questions
│   │   │   ├── eval_relevant_docs.json                 # Relevant documents for evaluation
│   │   │   ├── eval_corpus_embeddings_1.pt             # Version 1 embeddings
│   │   │   └── eval_corpus_embeddings_2.pt             # Version 2 embeddings
│   │   ├── Civil Law (Dan Su)/
│   │   │   ├── dan-su-0-1923.json                      # Raw documents
│   │   │   ├── dan-su-corpus.csv                       # Processed corpus
│   │   │   ├── dan-su-questions.csv                    # Questions
│   │   │   └── dan-su-qnc.csv                          # Question-answer pairs
│   │   ├── Criminal Law (Hinh Su)/
│   │   │   ├── hinh-su-0-3741.json                     # Raw documents
│   │   │   ├── hinh-su-corpus.csv                      # Processed corpus
│   │   │   ├── hinh-su-questions.csv                   # Questions
│   │   │   └── hinh-su-qnc.csv                         # Question-answer pairs
│   │   ├── Labor Law (Lao Dong)/
│   │   │   ├── lao-dong-0-911.json                     # Raw documents
│   │   │   ├── lao-dong-corpus.csv                     # Processed corpus
│   │   │   ├── lao-dong-questions.csv                  # Questions
│   │   │   └── lao-dong-qnc.csv                        # Question-answer pairs
│   │   └── Other Legal Domains/
│   │       ├── luat-bao-hiem-xa-hoi-*                  # Social Insurance Law
│   │       ├── luat-viec-lam-*                         # Employment Law
│   │       ├── luat-hon-nhan-va-gia-dinh-*             # Marriage and Family Law
│   │       ├── luat-cong-doan-*                        # Trade Union Law
│   │       ├── luat-bao-ve-quyen-loi-nguoi-tieu-dung-* # Consumer Protection Law
│   │       ├── luat-an-toan-ve-sinh-lao-dong-*         # Occupational Safety Law
│   │       └── hien-phap-*                             # Constitution
│   ├── preprocess.py                                   # Data preprocessing script
│   ├── preprocess.ipynb                                # Interactive preprocessing notebook
│
└── docker-compose.yaml                                 # Container orchestration
```

## Detailed Component Description

### Frontend Components

#### Core Application Files
- `src/App.js`: Main application component that handles routing and layout
- `src/index.js`: Application entry point
- `src/config.js`: Application configuration and environment variables
- `src/normalize.css`: CSS reset for consistent styling across browsers

#### Chat Components
- `components/Chat/Chat.js`: Main chat interface with real-time messaging
- `components/Chat/ChatMessage.js`: Individual message component
- `components/Chat/ChatSession.js`: Chat session management
- `components/Chat/*Modal.js`: Various modal components for chat operations
  - New session creation
  - Session renaming
  - Source management
  - Session deletion

#### Authentication Components
- `components/SignIn.js`: User sign-in interface
- `components/SignUp.js`: User registration interface
- `components/SignUp.module.css`: Styling for sign-up component
- `components/validate.js`: Form validation utilities

#### Utility Components
- `components/toast.js`: Toast notification system
- `reportWebVitals.js`: Performance monitoring
- `setupTests.js`: Test configuration

#### Configuration Files
- `nginx.conf`: Nginx configuration for serving the React application in production
- `Dockerfile`: Production Docker configuration using Nginx
- `Dockerfile_without_nginx`: Development Docker configuration without Nginx
- `package.json`: Node.js project configuration and dependencies

### Backend Components

#### Core Application Files
- `server_stream.py`: Main FastAPI application with streaming support for real-time chat
- `swagger.json`: OpenAPI/Swagger documentation for API endpoints
- `models.py`: SQLAlchemy database models for data persistence
- `wsgi.py`: WSGI entry point for production deployment
- `gunicorn_config.py`: Gunicorn server configuration for production

#### LLM Integration (`pythonllm/`)
- `handle_llm.py`: Core LLM integration
  - Model initialization and configuration
  - Response generation
  - Context management
- `handle_qdrant.py`: Vector database operations
  - Document indexing
  - Similarity search
  - Vector storage management
- `handle_graph.py`: Knowledge graph operations
  - Graph construction
  - Relationship management
  - Query processing
- `handle_retriever.py`: Document retrieval system
  - Context-aware retrieval
  - Relevance scoring
  - Document ranking

#### Embedding System (`embedding/`)
- Versioned embedding models and outputs
  - `output_v1/`: First version of embeddings
  - `output_v2/`: Second version of embeddings
- Pre-computed embeddings
  - `corpus_embeddings_v1.pt`: Version 1 corpus embeddings
  - `corpus_embeddings_v2.pt`: Version 2 corpus embeddings

#### Data Management (`data/`)
- `all_docs.json`: Collection of legal documents
- `all_doc_metas.json`: Metadata for legal documents
  - Document properties
  - Relationships
  - Categories

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

### Dataset Structure

#### Raw Data (`raw_data/`)
- Original legal documents organized by legal domains
- Each domain contains relevant legal texts and regulations
- `legal-conversation-v2.zip`: Dataset of legal conversations for training

#### Processed Data (`processed_data/`)
- **Evaluation Data**
  - Corpus and questions for model evaluation
  - Pre-computed embeddings for evaluation
  - Relevant document mappings

- **Domain-Specific Data**
  Each legal domain contains:
  - Raw JSON documents (`*-0-*.json`)
  - Processed corpus in CSV format (`*-corpus.csv`)
  - Questions dataset (`*-questions.csv`)
  - Question-answer pairs (`*-qnc.csv`)

- **Data Processing**
  - `preprocess.py`: Main preprocessing script
  - `preprocess.ipynb`: Interactive development and testing
  - `processing.log`: Detailed processing logs
  - `result.txt`: Processing results and statistics

#### Data Processing Pipeline
1. Raw documents are collected from various legal sources
2. Documents are preprocessed and structured
3. Questions and answers are generated/extracted
4. Data is split into training and evaluation sets
5. Embeddings are computed for semantic search

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