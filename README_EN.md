<p align="center">
  <img src="docs/images/hero-banner.png" alt="Memory Hub" width="100%">
</p>

<h1 align="center">Memory Hub - Multi-Agent Memory System</h1>

<p align="center">
  <img src="logo/memory-hub-logo.png" alt="Logo" width="128" height="128">
</p>

<p align="center">
  <strong>Give AI agents long-term memory for better conversations</strong>
</p>

<p align="center">
  <a href="https://github.com/wenhao4126/memory-hub">
    <img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Version">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  </a>
  <a href="docker-compose.yml">
    <img src="https://img.shields.io/badge/docker-ready-brightgreen.svg" alt="Docker">
  </a>
</p>

---

## 🎯 What is this?

**Memory Hub** is an **agent memory management system** that solves the "forgetfulness" problem of AI agents.

### Pain Points

Have you ever encountered these situations:

- 🔴 AI forgets what you told it last time
- 🔴 Each AI assistant has isolated memory, no information sharing
- 🔴 Only keyword search, cannot understand semantics
- 🔴 Chat history grows, hard to find key points

### What can Memory Hub do?

```
┌─────────────────────────────────────────────────────────┐
│  You: I'm Hanhuo, like sarcastic style, hate nonsense   │
│       ↓ Store to Memory Hub                              │
│  Next conversation...                                    │
│  AI: Hey Hanhuo! Here's a concise sarcastic reply 😄   │
│       ↑ Recall your preference from Memory Hub          │
└─────────────────────────────────────────────────────────┘
```

**Core Capabilities:**

- 🤖 **Multi-Agent Management**: Support multiple AI assistants registration and identity
- 💾 **Unified Memory Storage**: Four memory types - fact, preference, skill, experience
- 🔍 **Semantic Search**: Not keyword matching, but understanding meaning
- 🔄 **Smart Forgetting**: Automatically clean up unimportant old memories
- 🌐 **RESTful API**: Standard HTTP interface, easy integration

---

## 🏗️ System Architecture

<p align="center">
  <img src="docs/images/architecture-diagram.png" alt="Architecture" width="100%">
</p>

### Overall Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Layer                              │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│   │ Search  │  │ Coder   │  │ Writer  │  │ Analyst │       │
│   │ Agent   │  │ Agent   │  │ Agent   │  │ Agent   │       │
│   └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘       │
└────────┼────────────┼────────────┼────────────┼─────────────┘
         │            │            │            │
         └────────────┴─────┬──────┴────────────┘
                            │ HTTP API
                   ┌────────▼────────┐
                   │   Memory Hub    │
                   │   (FastAPI)     │
                   └────────┬────────┘
                            │
                   ┌────────▼────────┐
                   │   PostgreSQL    │
                   │   + pgvector    │
                   └─────────────────┘
```

### Memory Types

Memory Hub supports four memory types:

| Type | Description | Example |
|------|-------------|---------|
| 📌 Fact | Factual information | "User lives in Shanghai" |
| ❤️ Preference | User preferences | "Likes concise answers" |
| 🛠️ Skill | Skills and capabilities | "Can write Python code" |
| 📖 Experience | Past experiences | "Solved issue with Solution A" |

---

## 📦 Project Structure

```
memory-hub/
├── docker-compose.yml      # Docker orchestration
├── .env.example            # Environment template
├── .gitignore              # Git ignore config
│
├── backend/                # Backend code
│   ├── Dockerfile          # API service image
│   ├── app/
│   │   ├── main.py         # FastAPI entry
│   │   ├── config.py       # Configuration
│   │   ├── database.py     # Database connection
│   │   ├── api/            # API routes
│   │   ├── models/         # Data models
│   │   └── services/       # Business services
│   │
│   └── requirements.txt    # Python dependencies
│
├── scripts/                # Scripts
│   ├── start.sh            # One-click start
│   ├── backup.sh           # Database backup
│   └── init-db.sql         # Database init
│
└── docs/                   # Documentation
    ├── QUICKSTART.md       # 5-minute guide
    ├── USER_GUIDE.md       # User manual
    ├── ARCHITECTURE.md     # Architecture design
    └── API.md              # API reference
```

---

## 🚀 Quick Start

### Prerequisites

- ✅ Docker & Docker Compose (required)
- ✅ Python 3.10+ (for local development only)

### 1️⃣ Clone Project

```bash
git clone https://github.com/wenhao4126/memory-hub.git
cd memory-hub
```

### 2️⃣ Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit config (optional, defaults work)
vim .env
```

### 3️⃣ One-Click Start

#### Method 1: Easy Start (Recommended for Beginners) ✨

Designed for beginners, auto-handles Docker permissions and environment:

```bash
# Interactive menu
./scripts/quick-start.sh

# Or direct start
./scripts/quick-start.sh start
```

**Features:**
- ✅ Auto-check Docker installation and permissions
- ✅ Auto-handle permission issues
- ✅ Auto-check port conflicts
- ✅ Auto-create .env file
- ✅ Friendly interactive menu

#### Method 2: Standard Start

```bash
# Start all services (DB + API + pgAdmin)
./scripts/start.sh start
```

**Service URLs:**
- 📚 API Docs: http://localhost:8000/docs
- 🔌 API: http://localhost:8000/api/v1
- 🗄️ Database: localhost:5432
- 🛠️ pgAdmin: http://localhost:5050

### 4️⃣ Other Commands

```bash
# Check service status
./scripts/start.sh status

# View logs
./scripts/start.sh logs

# Stop services
./scripts/start.sh stop

# Test API
./scripts/start.sh test

# Clean data (dangerous⚠️)
./scripts/start.sh clean
```

---

## 💻 Usage Examples

### Example 1: Create Agent

```bash
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Writer",
    "description": "Content expert, good at writing",
    "capabilities": ["writing", "translation", "polishing"],
    "metadata": {"team_id": "003"}
  }'
```

**Response:**
```json
{
  "message": "Agent created successfully, ID: 550e8400-e29b-41d4-a716-446655440000"
}
```

### Example 2: Create Memory

```bash
curl -X POST http://localhost:8000/api/v1/memories \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "content": "User likes concise answers, hates nonsense",
    "memory_type": "preference",
    "importance": 0.8,
    "tags": ["user_preference", "communication_style"]
  }'
```

### Example 3: Semantic Search

```bash
curl -X POST http://localhost:8000/api/v1/memories/search/text \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What kind of answers does user like?",
    "limit": 5
  }'
```

**Response:**
```json
[
  {
    "id": "memory_id",
    "content": "User likes concise answers, hates nonsense",
    "similarity": 0.92,
    "memory_type": "preference",
    "importance": 0.8
  }
]
```

### Example 4: Enhanced Chat (Core Feature) 🚀

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "550e8400-e29b-41d4-a716-446655440000",
    "session_id": "session_123",
    "user_message": "Hello, help me write some content",
    "use_memory": true,
    "use_history": true,
    "auto_extract": true
  }'
```

**Workflow:**
1. Retrieve relevant memories (vector search)
2. Get conversation history
3. Generate personalized response with LLM
4. Record conversation to database
5. Auto-extract new memories

---

## 📚 Documentation

| Doc | Description | Audience |
|-----|-------------|----------|
| [Quick Start](docs/QUICKSTART.md) | 5-minute guide | Beginners |
| [User Guide](docs/USER_GUIDE.md) | Detailed usage | Users |
| [Architecture](docs/ARCHITECTURE.md) | System design | Developers |
| [API Reference](docs/API.md) | RESTful API docs | Developers |

---

## 🗄️ Data Models

### Agents

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR | Agent name |
| description | TEXT | Description |
| capabilities | TEXT[] | Capability tags |
| metadata | JSONB | Extended info |
| created_at | TIMESTAMP | Created time |
| updated_at | TIMESTAMP | Updated time |

### Memories

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| agent_id | UUID | Associated agent |
| content | TEXT | Memory content |
| embedding | vector(1024) | Vector embedding (text-embedding-v4) |
| memory_type | VARCHAR | Type: fact/preference/skill/experience |
| importance | FLOAT | Importance 0-1 |
| access_count | INTEGER | Access count |
| tags | TEXT[] | Tags |
| created_at | TIMESTAMP | Created time |
| last_accessed | TIMESTAMP | Last access time |
| expires_at | TIMESTAMP | Expiration time |

---

## 🔧 Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| DB_HOST | localhost | Database host |
| DB_PORT | 5432 | Database port |
| DB_USER | memory_user | Database user |
| DB_PASSWORD | memory_pass_2026 | Database password |
| DB_NAME | memory_hub | Database name |
| API_HOST | 0.0.0.0 | API listen address |
| API_PORT | 8000 | API port |
| API_DEBUG | false | Debug mode |
| EMBEDDING_MODEL | text-embedding-v4 | Embedding model |
| EMBEDDING_DIMENSION | 1024 | Vector dimension |
| DASHSCOPE_API_KEY | - | Alibaba DashScope API Key |

### Production Deployment

⚠️ **Must change before deployment:**

1. `DB_PASSWORD` - Use strong password
2. `ADMIN_PASSWORD` - Use strong password
3. `API_DEBUG` - Set to `false`
4. Configure firewall, restrict port access

---

## 🐳 Docker Commands

### One-Click Scripts (Recommended)

```bash
# Start
./scripts/start.sh start

# Status
./scripts/start.sh status

# Logs
./scripts/start.sh logs

# Stop
./scripts/start.sh stop

# Test
./scripts/start.sh test
```

### Manual Docker Commands

```bash
# Start all services
docker-compose up -d

# View status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes (dangerous⚠️)
docker-compose down -v

# Enter database container
docker exec -it memory-hub-db psql -U memory_user -d memory_hub

# pgAdmin
# Visit http://localhost:5050
# Email: admin@memory.hub
# Password: admin123
```

### Backup & Restore

```bash
# Create backup
./scripts/backup.sh create

# List backups
./scripts/backup.sh list

# Restore backup
./scripts/backup.sh restore

# Clean old backups (keep last 5)
./scripts/backup.sh clean 5
```

---

## 🧪 Testing

```bash
# Enter backend directory
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=app --cov-report=term-missing
```

**Test Coverage:**
- ✅ API endpoint tests: 33 tests
- ✅ Service layer tests: 28 tests
- ✅ Total coverage: 77% (core logic >85%)

---

## 📋 Roadmap

### Completed ✅

- [x] Day 1: Project structure, Docker environment, database
- [x] Day 2: Vector embedding, memory storage API, unit tests
- [x] Day 3: Multi-agent collaboration, memory sharing API
- [x] Day 4: Vector search, monitoring and logging
- [x] Day 5: Performance optimization, documentation, deployment scripts

### In Progress 🚧

- [ ] Knowledge base management
- [ ] Conversation history management
- [ ] Auto memory extraction optimization

### Planned 📅

- [ ] Web management interface
- [ ] Memory visualization
- [ ] Multi-tenant support

---

## 🤝 Contributing

Contributions welcome! Please follow these steps:

1. Fork this repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Submit Pull Request

---

## 📄 License

This project is licensed under MIT License - see [LICENSE](LICENSE) file

---

## 👥 Author

- **Xiao Ma** - *Project Development* - Shaniu Team 💻

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern high-performance web framework
- [pgvector](https://github.com/pgvector/pgvector) - PostgreSQL vector extension
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation library
- [DashScope](https://dashscope.aliyun.com/) - Alibaba Qwen API

---

## 🛠️ Optimization (2026-03-17)

- ✅ Docker image: 12.7GB → 613MB (95% reduction)
- ✅ Removed large dependencies (sentence-transformers, etc.)
- ✅ Cleaned pip and huggingface caches (4.6GB)
- ✅ Data volume migrated to ext4 partition
- ✅ Configured systemd auto-start service

---

> 💡 **Tip**: Code is written for humans to read, and incidentally for machines to execute!

---

*Memory Hub v0.1.0 - 2026.03.09*