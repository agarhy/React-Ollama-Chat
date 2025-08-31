# AI Chat Application - Docker Setup

A containerized full-stack chatbot application with React frontend, Python FastAPI backend, and Ollama AI integration.

## image
![AI Chat Application Screenshot](https://github.com/agarhy/React-Ollama-Chat/.blob/image1.png)
![AI Chat Application Screenshot](https://github.com/agarhy/React-Ollama-Chat/.blob/image2.png)

## 🚀 Quick Start with Docker

### Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 8GB RAM (for AI models)
- 10GB free disk space

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ai-chat
```

### 2. Start the Application

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### 3. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Ollama API**: http://localhost:12500

## 📁 Project Structure

```
ai-chat/
├── docker/
│   ├── ollama/
│   │   ├── Dockerfile
│   │   └── pull-models.sh
│   └── app/
│       ├── Dockerfile
│       └── start.sh
├── backend/
├── frontend/
├── data/                 # Database files (mounted volume)
├── ollama/models/        # Ollama models (mounted volume)
├── docker-compose.yml
├── .env
└── README-Docker.md
```

## 🐳 Container Architecture

### Services

1. **ollama** - AI model server
   - Image: Custom Ollama container
   - Port: 12500:11434
   - Models: phi3:mini, mistral:latest
   - Volume: ./ollama/models

2. **app** - Full-stack application
   - Image: Custom Node.js + Python container
   - Ports: 3000:3000 (frontend), 8000:8000 (backend)
   - Volume: ./data (database)
   - Depends on: ollama

### Networking

- Custom bridge network: `ai-chat-network`
- Internal communication: `ollama:11434`
- External access: `localhost:12500`

## ⚙️ Configuration

### Environment Variables

Create `.env` file (copy from `.env.example`):

```bash
# Ollama Configuration
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
OLLAMA_BASE_URL=http://ollama:11434

# Database Configuration
DATABASE_TYPE=sqlite
DATABASE_PATH=/app/data/conversations.db

# Application Configuration
APP_HOST=0.0.0.0
APP_PORT=8000
DEBUG=false
```

### Custom Configuration

1. **Change Ollama Models**: Edit `docker/ollama/pull-models.sh`
2. **Database Type**: Modify `DATABASE_TYPE` in `.env`
3. **Ports**: Update `docker-compose.yml` ports section

## 🔧 Development

### Building Images

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build ollama
docker-compose build app

# Force rebuild
docker-compose build --no-cache
```

### Debugging

```bash
# View logs
docker-compose logs ollama
docker-compose logs app

# Execute commands in containers
docker-compose exec ollama bash
docker-compose exec app bash

# Check container status
docker-compose ps
```

### Local Development

For development with hot reload:

```bash
# Start only Ollama
docker-compose up ollama -d

# Run backend locally
cd backend
source ../aichatenv/bin/activate
python -m backend

# Run frontend locally
cd frontend
npm start
```

## 📊 Features

### Core Features
- ✅ Multi-model AI chat (phi3:mini, mistral:latest)
- ✅ Conversation management with auto-generated titles
- ✅ Real-time chat with loading indicators
- ✅ Conversation history and persistence
- ✅ Modern responsive UI with sidebar navigation

### Enhanced Features
- ✅ **Online Search**: DuckDuckGo integration (toggle in UI)
- ✅ **Date/Time Awareness**: Current datetime context
- ✅ **Conversation Management**: Delete conversations with confirmation
- ✅ **Fixed Layout**: Proper scrolling (chat area only)
- ✅ **Docker Deployment**: Full containerization

## 🗄️ Data Persistence

### Volumes

- `./data/` - SQLite database files
- `./ollama/models/` - Downloaded AI models


### Backup

```bash
# Backup database
cp data/conversations.db data/conversations.backup.db

# Backup models (optional, can be re-downloaded)
tar -czf ollama-models-backup.tar.gz ollama/models/
```

## 🚨 Troubleshooting

### Common Issues

1. **Ollama not starting**
   ```bash
   docker-compose logs ollama
   # Check if models are downloading
   ```

2. **App can't connect to Ollama**
   ```bash
   docker-compose exec app curl http://ollama:11434/api/tags
   ```

3. **Port conflicts**
   ```bash
   # Change ports in docker-compose.yml
   ports:
     - "3001:3000"  # Frontend
     - "8001:8000"  # Backend
     - "12501:11434" # Ollama
   ```

4. **Out of memory**
   ```bash
   # Reduce models or increase Docker memory limit
   # Remove unused models:
   docker-compose exec ollama ollama rm mistral:latest
   ```

### Performance Optimization

1. **Faster startup**: Pre-pull models
   ```bash
   docker-compose exec ollama ollama pull phi3:mini
   ```

2. **Reduce memory usage**: Use smaller models
   ```bash
   # Edit docker/ollama/pull-models.sh
   ollama pull phi3:mini  # Keep only this
   ```

## 📝 API Usage

### Chat with Search

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the latest news about AI?",
    "model": "phi3:mini",
    "enable_search": true
  }'
```

### List Models

```bash
curl http://localhost:8000/models
```

### Get Conversations

```bash
curl http://localhost:8000/conversations
```

## 🔄 Updates and Maintenance

### Update Models

```bash
docker-compose exec ollama ollama pull phi3:mini
docker-compose exec ollama ollama pull mistral:latest
```

### Update Application

```bash
git pull
docker-compose build
docker-compose up -d
```

### Clean Up

```bash
# Remove containers and networks
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

## 📄 License

This project is licensed under the MIT License.
