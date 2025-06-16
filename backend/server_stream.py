from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from dotenv import load_dotenv
import os
import traceback
import logging
from datetime import timedelta
from flask_swagger_ui import get_swaggerui_blueprint
import sys
from flask_migrate import Migrate
import time
import json
from pprint import pprint
import threading
import queue
import hmac
import hashlib
import requests

from models import db, bcrypt, User, ChatSession, ChatHistory

# Add pythonLLM directory to PYTHONPATH
current_dir = os.path.dirname(os.path.abspath(__file__))
pythonllm_dir = os.path.join(current_dir, "pythonllm")
sys.path.append(pythonllm_dir)
from handle_graph import my_graph

# Load environment variables first
load_dotenv()

# Check required environment variables
required_env_vars = ['JWT_SECRET_KEY', 'DB_USER', 'DB_PASSWORD',
                     'DB_HOST', 'DB_PORT', 'DB_NAME',
                     'QDRANT_URL', 'QDRANT_COLLECTION_NAME',
                     'FACEBOOK_PAGE_ACCESS_TOKEN', 'FACEBOOK_APP_SECRET',
                     'FACEBOOK_PAGE_ID', 'FACEBOOK_VERIFY_TOKEN']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = Flask(__name__)
CORS(app)

# Swagger configuration
SWAGGER_URL = '/api/docs'  # URL for exposing Swagger UI
API_URL = '/static/swagger.json'  # Our API url (can of course be a local resource)

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "Law Chatbot API"
    }
)

# Register blueprint at URL
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Create swagger.json
@app.route("/static/swagger.json")
def send_swagger_json():
    swagger_json = {
        "swagger": "2.0",
        "info": {
            "title": "Law Chatbot API",
            "description": "API documentation for Law Chatbot",
            "version": "1.0.0"
        },
        "basePath": "/",
        "schemes": ["http"],
        "consumes": ["application/json"],
        "produces": ["application/json"],
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Authorization header using the Bearer scheme. Example: \"Bearer {token}\""
            }
        },
        "paths": {
            "/register": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Register a new user",
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string"},
                                    "username": {"type": "string"},
                                    "password": {"type": "string"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "User registered successfully"
                        }
                    }
                }
            },
            "/login": {
                "post": {
                    "tags": ["Authentication"],
                    "summary": "Login user",
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string"},
                                    "password": {"type": "string"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Login successful",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "access_token": {"type": "string"}
                                }
                            }
                        },
                        "401": {
                            "description": "Invalid credentials"
                        }
                    }
                }
            },
            "/api/profile": {
                "get": {
                    "tags": ["User"],
                    "summary": "Get user profile information",
                    "security": [{"Bearer": []}],
                    "responses": {
                        "200": {
                            "description": "User profile information",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string"},
                                    "username": {"type": "string"}
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized access"
                        }
                    }
                }
            },
            "/api/sessions": {
                "get": {
                    "tags": ["Chat Sessions"],
                    "summary": "Get all chat sessions for the current user",
                    "security": [{"Bearer": []}],
                    "responses": {
                        "200": {
                            "description": "List of chat sessions",
                            "schema": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "id": {"type": "integer"},
                                        "name": {"type": "string"},
                                        "created_at": {"type": "string", "format": "date-time"}
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized access"
                        }
                    }
                },
                "post": {
                    "tags": ["Chat Sessions"],
                    "summary": "Create a new chat session",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": "Chat session created successfully",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "session_id": {"type": "integer"},
                                    "name": {"type": "string"}
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized access"
                        }
                    }
                }
            },
            "/api/sessions/{session_id}": {
                "put": {
                    "tags": ["Chat Sessions"],
                    "summary": "Rename a chat session",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "session_id",
                            "in": "path",
                            "required": True,
                            "type": "integer",
                            "description": "ID of the chat session"
                        },
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"}
                                }
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Chat session renamed successfully",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "integer"},
                                    "name": {"type": "string"},
                                    "created_at": {"type": "string", "format": "date-time"}
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized access"
                        },
                        "404": {
                            "description": "Session not found"
                        }
                    }
                },
                "delete": {
                    "tags": ["Chat Sessions"],
                    "summary": "Delete a chat session",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "session_id",
                            "in": "path",
                            "required": True,
                            "type": "integer",
                            "description": "ID of the chat session"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Chat session deleted successfully"
                        },
                        "401": {
                            "description": "Unauthorized access"
                        },
                        "404": {
                            "description": "Session not found"
                        }
                    }
                }
            },
            "/api/chat": {
                "post": {
                    "tags": ["Chat"],
                    "summary": "Send a message to the chatbot",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "session_id": {"type": "integer"},
                                    "messages": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "role": {"type": "string"},
                                                "content": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Chat response",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "response": {"type": "string"}
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized access"
                        },
                        "500": {
                            "description": "Internal server error"
                        }
                    }
                }
            },
            "/api/chat-stream": {
                "post": {
                    "tags": ["Chat Stream"],
                    "summary": "Send a message to the chatbot and get a stream of response",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "body",
                            "in": "body",
                            "required": True,
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "session_id": {"type": "integer"},
                                    "messages": {
                                        "type": "array",
                                        "items": {
                                            "type": "object",
                                            "properties": {
                                                "role": {"type": "string"},
                                                "content": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Server-Sent Events stream of chat response",
                            "schema": {
                                "type": "string",
                                "format": "text/event-stream"
                            },
                            "headers": {
                                "Content-Type": {
                                    "type": "string",
                                    "description": "text/event-stream"
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized access"
                        },
                        "500": {
                            "description": "Internal server error"
                        }
                    }
                }
            },
            "/api/history/{session_id}": {
                "get": {
                    "tags": ["Chat History"],
                    "summary": "Get chat history for a specific session",
                    "security": [{"Bearer": []}],
                    "parameters": [
                        {
                            "name": "session_id",
                            "in": "path",
                            "required": True,
                            "type": "integer",
                            "description": "ID of the chat session"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Chat history",
                            "schema": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "role": {"type": "string"},
                                        "content": {"type": "string"},
                                        "timestamp": {"type": "string", "format": "date-time"}
                                    }
                                }
                            }
                        },
                        "401": {
                            "description": "Unauthorized access"
                        }
                    }
                }
            }
        }
    }
    return jsonify(swagger_json)

jwt_key = os.getenv('JWT_SECRET_KEY')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_host = os.getenv('DB_HOST')
db_port = os.getenv('DB_PORT')
db_name = os.getenv('DB_NAME')

# Facebook Messenger configuration
PAGE_ACCESS_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('FACEBOOK_VERIFY_TOKEN')
PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')
APP_SECRET = os.getenv('FACEBOOK_APP_SECRET')
# Set to store processed message IDs
processed_messages = set()

if os.getenv('FLASK_ENV', 'development') == 'production':
    app.config['DEBUG'] = False 
else:
    app.config['DEBUG'] = True 
app.logger.setLevel(logging.INFO)

# Configure database for PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = jwt_key
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# Set JWT expiration time
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=2)

db.init_app(app)
with app.app_context():
    db.create_all()
jwt = JWTManager(app)
migrate = Migrate(app, db)

@jwt.unauthorized_loader
def unauthorized_callback(err_msg):
    print(f"Unauthorized error: {err_msg}")
    return jsonify({"error": "Unauthorized access"}), 401

@jwt.invalid_token_loader
def invalid_token_callback(err_msg):
    print(f"Invalid token error: {err_msg}")
    return jsonify({"error": "Invalid token"}), 422

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email')
        username = data.get('username')
        password = data.get('password')

        # Validate required fields
        if not all([email, username, password]):
            return jsonify({'error': 'All fields are required'}), 400

        # Validate email format
        if not '@' in email or not '.' in email:
            return jsonify({'error': 'Invalid email format'}), 400

        # Validate password length
        if len(password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400

        # Check if email or username already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already taken'}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(email=email, password=hashed_password, username=username)
        db.session.add(new_user)
        db.session.commit()

        return jsonify({'message': 'User registered successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            access_token = create_access_token(identity=str(user.id))
            return jsonify({
                'access_token': access_token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username
                }
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions', methods=['POST'])
@jwt_required()
def create_session():
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Session name is required'}), 400
            
        session_name = data.get('name').strip()
        if not session_name:
            return jsonify({'error': 'Session name cannot be empty'}), 400

        new_session = ChatSession(
            user_id=user_id,
            name=session_name,
            chat_history=[],
            summary=[],
            last_document=[]
        )
        db.session.add(new_session)
        db.session.commit()

        return jsonify({
            'session_id': new_session.id,
            'name': new_session.name,
            'created_at': new_session.created_at.isoformat(),
            'updated_at': new_session.updated_at.isoformat(),
            'chat_history': new_session.chat_history,
            'summary': new_session.summary,
            'last_document': new_session.last_document
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = get_jwt_identity()
    user = User.query.filter_by(id=user_id).first()
    return jsonify({'email': user.email, 'username': user.username}), 200

@app.route('/api/sessions', methods=['GET'])
@jwt_required()
def get_sessions():
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'error': 'Invalid user'}), 401

        sessions = ChatSession.query.filter_by(user_id=user_id)\
            .order_by(ChatSession.created_at.desc())\
            .all()
            
        return jsonify([
            {
                'id': session.id,
                'name': session.name,
                'created_at': session.created_at.isoformat(),
                'updated_at': session.updated_at.isoformat(),
                'chat_history': session.chat_history or [],  # Return empty list if None
                'summary': session.summary or [],             # Return empty list if None
                'last_document': session.last_document or []   # Return empty list if None
            }
            for session in sessions
        ]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>', methods=['PUT'])
@jwt_required()
def rename_session(session_id):
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        if not data or 'name' not in data:
            return jsonify({'error': 'New name is required'}), 400
            
        new_name = data.get('name').strip()
        if not new_name:
            return jsonify({'error': 'New name cannot be empty'}), 400

        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        session.name = new_name
        db.session.commit()

        return jsonify({
            'id': session.id,
            'name': session.name,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'chat_history': session.chat_history or [],  # Return empty list if None
            'summary': session.summary or [],             # Return empty list if None
            'last_document': session.last_document or []   # Return empty list if None
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/sessions/<int:session_id>', methods=['DELETE'])
@jwt_required()
def delete_session(session_id):
    try:
        user_id = get_jwt_identity()

        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        # Delete related chat history
        ChatHistory.query.filter_by(session_id=session_id).delete()

        db.session.delete(session)
        db.session.commit()

        return jsonify({'message': 'Session deleted successfully'}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 422

@app.route('/api/chat', methods=['POST'])
@jwt_required()
def chat():
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        session_id = data.get('session_id')
        messages = data.get('messages', [])
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        if not messages:
            return jsonify({'error': 'Messages are required'}), 400
            
        # Verify session belongs to user
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        # print("session: ", session)
        # print("session.chat_history: ", session.chat_history)
        # print("session.summary: ", session.summary)
        # print("session.last_document: ", session.last_document)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        msg = messages[-1]
        if not msg.get('content'):
            return jsonify({'error': 'Message content is required'}), 400

        # Save user message to chat history
        new_message = ChatHistory(session_id=session_id, role=msg['role'], content=msg['content'])
        db.session.add(new_message)

        # Get last state from session's chat_history
        last_state = dict()
        if session.chat_history:
            last_state["chat_history"] = [(item[0], item[1]) for item in session.chat_history]
        if session.summary:
            last_state["summary"] = session.summary
        if session.last_document:
            last_state["documents"] = session.last_document
        # print("last_state: ", last_state)

        # Get RAG pipeline response with context
        # current_state = get_response(msg['content'], last_state)
        if last_state:
            last_state["question"] = msg['content']
            inputs = last_state
        else:
            inputs = {"question": msg['content']}
        print("inputs: ")
        pprint(inputs)

        start_time = time.time()
        for step in my_graph.stream(inputs):
            for node_name, state in step.items():
                # Node
                print(f"Node '{node_name}':")
                # Optional: print full state at each node
                pprint(state, indent=2, width=80, depth=None)
            print("\n---\n")
        current_state = state
        end_time = time.time()
        
        if not current_state:
            return jsonify({
                'error': 'Failed to get response from AI',
                'response': 'Failed to get response from AI'
            }), 500
            
        response = current_state["generation"]

        # Format sources
        sources = []
        for doc_content in current_state.get("documents", []):
            sources.append(f"- {doc_content}")

        response += "\n\nSOURCES OF INFORMATION:\n" + "\n\n".join(sources)

        # Save AI response to chat history
        new_message = ChatHistory(session_id=session_id, role='AI', content=response)
        db.session.add(new_message)
        
        # Update session's chat_history with new state
        if not session.chat_history:
            session.chat_history = []
        if current_state.get("chat_history", []):
            session.chat_history = current_state.get("chat_history", [])
        if not session.summary:
            session.summary = []
        if current_state.get("summary", []):
            session.summary = current_state.get("summary", [])
        if not session.last_document:
            session.last_document = []
        if current_state.get("documents", []):
            session.last_document = current_state.get("documents", [])
        
        db.session.commit()

        return jsonify({
            'response': response,
            'processing_time': end_time - start_time,
            'session_state': current_state
        }), 200
    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Generator chính để yield từ message_queue
def send_message(message_queue):
    while True:
        try:
            message = message_queue.get(timeout=0.1)
            print(f">>> message: {message}")
            if message == "__DONE__":
                break
            yield message
        except queue.Empty:
            continue
    
@app.route('/api/chat-stream', methods=['POST'])
@jwt_required()
def chat_stream():
    try:
        user_id = get_jwt_identity()
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        session_id = data.get('session_id')
        messages = data.get('messages', [])
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        if not messages:
            return jsonify({'error': 'Messages are required'}), 400
            
        # Verify session belongs to user
        session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
        # print("session: ", session)
        # print("session.chat_history: ", session.chat_history)
        # print("session.summary: ", session.summary)
        # print("session.last_document: ", session.last_document)
        if not session:
            return jsonify({'error': 'Session not found'}), 404

        msg = messages[-1]
        if not msg.get('content'):
            return jsonify({'error': 'Message content is required'}), 400

        # Save user message to chat history
        new_message = ChatHistory(session_id=session_id, role=msg['role'], content=msg['content'])
        db.session.add(new_message)
        db.session.commit()

        # Get last state from session's chat_history
        last_state = dict()
        if session.chat_history:
            last_state["chat_history"] = [(item[0], item[1]) for item in session.chat_history]
        if session.summary:
            last_state["summary"] = session.summary
        if session.last_document:
            last_state["documents"] = session.last_document
        # print("last_state: ", last_state)

        # Get RAG pipeline response with context
        # current_state = get_response(msg['content'], last_state)
        if last_state:
            last_state["question"] = msg['content']
            inputs = last_state
        else:
            inputs = {"question": msg['content']}

        inputs["node_start"] = ["start"]
        inputs["this_node"] = []

        # Create a queue for sending messages to client
        message_queue = queue.Queue()

        # Thread function to monitor node_start changes
        def monitor_node_start(state, message_queue, stop_event):
            last_node = "start"
            while True:
                current_node = state.get("node_start", None)
                if current_node and current_node[-1] != last_node:
                    # print(f">>> START executing node: {current_node[-1]}")
                    if current_node[-1] == "update_memory":
                        response = state["this_node"][-1]["generation"]

                        # Format sources
                        sources = []
                        for doc_content in state["this_node"][-1].get("documents", []):
                            sources.append(f"- {doc_content}")

                        response += "\n\nSOURCES OF INFORMATION:\n" + "\n\n".join(sources)
                        
                        # Send the last response
                        message_queue.put(f"data: {json.dumps({'type': 'response', 'content': response}, ensure_ascii=False)}\n\n")
                        message_queue.put(f"data: {json.dumps({'type': 'done'})}\n\n")
                        message_queue.put("__DONE__")
                    else:
                        message_queue.put(f"data: {json.dumps({'type': 'step', 'node': current_node[-1]})}\n\n")
                    last_node = current_node[-1]
                if stop_event.is_set():
                    break
                time.sleep(0.1)  # Small delay to prevent high CPU usage

        # Start monitoring thread
        stop_monitor = threading.Event()
        monitor_thread = threading.Thread(target=monitor_node_start, args=(inputs, message_queue, stop_monitor), daemon=True)
        monitor_thread.start()

        # Thread function to process graph
        def enqueue_messages_from_graph(inputs):
            # Main processing loop
            for step in my_graph.stream(inputs):
                for node_name, state in step.items():
                    # yield f"data: {json.dumps({'type': 'step', 'node': node_name})}\n\n"
                    pass
            current_state = state
            stop_monitor.set()

            # Save AI response to chat history
            if current_state:
                response = current_state["generation"]

                # Format sources
                sources = []
                for doc_content in current_state.get("documents", []):
                    sources.append(f"- {doc_content}")

                response += "\n\nSOURCES OF INFORMATION:\n" + "\n\n".join(sources)
                
                # Send the last response
                message_queue.put(f"data: {json.dumps({'type': 'response', 'content': response}, ensure_ascii=False)}\n\n")
                message_queue.put(f"data: {json.dumps({'type': 'done'})}\n\n")
                message_queue.put("__DONE__")

                # Use app context for database operations
                with app.app_context():
                    new_message = ChatHistory(session_id=session_id, role='AI', content=response)
                    db.session.add(new_message)
                    
                    # Update session's chat_history with new state
                    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
                    if not session.chat_history:
                        session.chat_history = []
                    if current_state.get("chat_history", []):
                        session.chat_history = current_state.get("chat_history", [])
                    if not session.summary:
                        session.summary = []
                    if current_state.get("summary", []):
                        session.summary = current_state.get("summary", [])
                    if not session.last_document:
                        session.last_document = []
                    if current_state.get("documents", []):
                        session.last_document = current_state.get("documents", [])
                    
                    db.session.commit()
            monitor_thread.join()

        def generate():
            # Start thread để chạy graph
            graph_thread = threading.Thread(target=enqueue_messages_from_graph, args=(inputs,), daemon=True)
            graph_thread.start()
            yield from send_message(message_queue)

        return Response(stream_with_context(generate()), mimetype='text/event-stream')

    except Exception as e:
        db.session.rollback()
        print(f"Error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/history/<int:session_id>', methods=['GET'])
@jwt_required()
def history(session_id):
    user_id = get_jwt_identity()
    history = ChatHistory.query.filter_by(session_id=session_id).all()
    return jsonify([{'role': msg.role, 'content': msg.content, 'timestamp': msg.timestamp} for msg in history])

def verify_webhook_signature(request):
    """Verify that the webhook request is from Facebook"""
    signature = request.headers.get('X-Hub-Signature-256', '')
    if not signature:
        return False
    
    # Get the request body
    body = request.get_data()
    
    # Calculate expected signature
    expected_signature = 'sha256=' + hmac.new(
        APP_SECRET.encode('utf-8'),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Compare signatures
    return hmac.compare_digest(signature, expected_signature)

def split_message(message, max_length=1900):
    """Split long message into smaller chunks"""
    if len(message) <= max_length:
        return [message]
    
    chunks = []
    current_chunk = ""
    
    # Split by sentences first
    sentences = message.split('. ')
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 2 <= max_length:
            current_chunk += sentence + '. '
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + '. '
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def send_facebook_message(recipient_id, message_text):
    """Send message to user via Facebook Messenger"""
    url = f"https://graph.facebook.com/v17.0/{PAGE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {PAGE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Split message if it's too long
    message_chunks = split_message(message_text)
    results = []
    
    for chunk in message_chunks:
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": chunk}
        }
        try:
            print(f"Sending message chunk to {recipient_id}: {chunk[:50]}...")
            print(f"Using token: {PAGE_ACCESS_TOKEN[:10]}...")
            print(f"Using page ID: {PAGE_ID}")
            print(f"Request URL: {url}")
            response = requests.post(url, headers=headers, json=data)
            print(f"Facebook API Response: {response.status_code}")
            print(f"Response content: {response.text}")
            results.append(response.json())
        except Exception as e:
            print(f"Error sending message chunk: {str(e)}")
            results.append(None)
    
    return results

@app.route('/webhook', methods=['GET'])
def verify_webhook():
    """Verify webhook for Facebook Messenger"""
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    if mode and token:
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge
        return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    """Handle incoming messages from Facebook Messenger"""
    # Verify webhook signature
    if not verify_webhook_signature(request):
        print("Invalid webhook signature")
        return 'Invalid signature', 403

    data = request.get_json()
    print(f"Received webhook data: {data}")
    
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                # Check if message has been processed
                message_id = messaging_event.get('message', {}).get('mid')
                if message_id in processed_messages:
                    print(f"Message {message_id} already processed, skipping")
                    continue
                
                sender_id = messaging_event['sender']['id']
                
                if 'message' in messaging_event:
                    if 'text' in messaging_event['message']:
                        message_text = messaging_event['message']['text']
                        print(f"Received message from {sender_id}: {message_text}")
                        
                        try:
                            # Get or create Facebook user
                            facebook_user = User.query.filter_by(email=f"facebook_{sender_id}@facebook.com").first()
                            if not facebook_user:
                                # Create a new user for this Facebook user
                                facebook_user = User(
                                    email=f"facebook_{sender_id}@facebook.com",
                                    username=f"facebook_user_{sender_id}",
                                    password=bcrypt.generate_password_hash("facebook_user_password").decode('utf-8')
                                )
                                db.session.add(facebook_user)
                                db.session.commit()

                            # Get or create a session for this Facebook user
                            session = ChatSession.query.filter_by(user_id=facebook_user.id).first()
                            if not session:
                                session = ChatSession(
                                    user_id=facebook_user.id,
                                    name=f"Facebook Chat - {sender_id}",
                                    chat_history=[],
                                    summary=[],
                                    last_document=[]
                                )
                                db.session.add(session)
                                db.session.commit()

                            # Save user message to chat history
                            new_message = ChatHistory(session_id=session.id, role='user', content=message_text)
                            db.session.add(new_message)

                            # Get last state from session's chat_history
                            last_state = dict()
                            if session.chat_history:
                                last_state["chat_history"] = [(item[0], item[1]) for item in session.chat_history]
                            if session.summary:
                                last_state["summary"] = session.summary
                            if session.last_document:
                                last_state["documents"] = session.last_document

                            # Get RAG pipeline response with context
                            if last_state:
                                last_state["question"] = message_text
                                inputs = last_state
                            else:
                                inputs = {"question": message_text}

                            # Process through RAG pipeline
                            for step in my_graph.stream(inputs):
                                for node_name, state in step.items():
                                    pass
                            current_state = state

                            if not current_state:
                                error_message = "Xin lỗi, tôi không thể tạo câu trả lời lúc này. Vui lòng thử lại sau."
                                
                                # Send error message to user
                                results = send_facebook_message(sender_id, error_message)
                                if all(result and 'error' not in result for result in results):
                                    print(f"Error message sent successfully")
                                    processed_messages.add(message_id)
                                    if len(processed_messages) > 1000:
                                        processed_messages.clear()
                                else:
                                    print("Failed to send some message chunks")
                                continue

                            response = current_state["generation"]

                            # Format sources
                            sources = []
                            for doc_content in current_state.get("documents", []):
                                sources.append(f"- {doc_content}")

                            response_and_source = response + "\n\nSOURCES OF INFORMATION:\n" + "\n\n".join(sources)

                            # Save AI response to chat history
                            new_message = ChatHistory(session_id=session.id, role='AI', content=response_and_source)
                            db.session.add(new_message)
                            
                            # Update session's chat_history with new state
                            if not session.chat_history:
                                session.chat_history = []
                            if current_state.get("chat_history", []):
                                session.chat_history = current_state.get("chat_history", [])
                            if not session.summary:
                                session.summary = []
                            if current_state.get("summary", []):
                                session.summary = current_state.get("summary", [])
                            if not session.last_document:
                                session.last_document = []
                            if current_state.get("documents", []):
                                session.last_document = current_state.get("documents", [])
                            
                            db.session.commit()
                            
                            # Send response back to user
                            results = send_facebook_message(sender_id, response)
                            if all(result and 'error' not in result for result in results):
                                print(f"All message chunks sent successfully")
                                # Add message ID to processed set
                                processed_messages.add(message_id)
                                # Keep set size manageable
                                if len(processed_messages) > 1000:
                                    processed_messages.clear()
                            else:
                                print("Failed to send some message chunks")
                        except Exception as e:
                            print(f"Error processing message: {e}")
                            traceback.print_exc()
                            send_facebook_message(sender_id, "Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại sau.")
    
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, use_reloader=False)