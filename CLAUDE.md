# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Workspace Overview

This is a multi-project workspace containing three major AI and IoT projects:

1. **mem0** - An intelligent memory layer for AI assistants and agents
2. **xiaozhi-esp32-server** - Backend services for AI voice interaction system
3. **xiaozhi-esp32** - ESP32 firmware for AI chatbot hardware devices

## Project Architectures

### mem0 (Python Memory System)
- **Core Memory System** (`mem0/memory/`) - CRUD operations for AI memory management
- **Multi-provider Support** - Vector stores (Chroma, Pinecone, Qdrant), LLMs (OpenAI, Anthropic), embeddings
- **Graph Memory** (`mem0/graphs/`) - Knowledge graph capabilities with Neptune
- **Factory Pattern** - Modular provider system for different AI services
- **Async/Sync APIs** - Dual implementation for both sync and async usage

Key commands:
```bash
cd mem0
make install_all    # Install all dependencies
make format        # Format code with ruff
make lint          # Run linting
make test          # Run tests
hatch run test     # Alternative test runner
```

### xiaozhi-esp32-server (Multi-language Backend)
- **Python Core** (`xiaozhi-server/`) - WebSocket/HTTP server with AI integrations
- **Java API** (`manager-api/`) - Spring Boot management backend with Shiro security
- **Vue Web** (`manager-web/`) - Vue 2 management interface  
- **Uni-app Mobile** (`manager-mobile/`) - Cross-platform mobile app

Key commands:
```bash
# Python server
cd main/xiaozhi-server
pip install -r requirements.txt
python app.py

# Java API
cd main/manager-api
mvn clean compile
mvn test
mvn package

# Vue web
cd main/manager-web
npm install
npm run serve
npm run build

# Mobile app
cd main/manager-mobile
pnpm install
pnpm run dev:h5
pnpm run lint:fix
```

### xiaozhi-esp32 (ESP32 Firmware)
- **Multi-board Support** - 70+ ESP32 development boards
- **Audio Pipeline** - Wake word detection, ASR, TTS with various codecs
- **Display System** - LVGL GUI with OLED/LCD support
- **MCP Integration** - Model Context Protocol for device control
- **Dual Protocols** - WebSocket and MQTT+UDP communication

Key commands:
```bash
cd xiaozhi-esp32
idf.py build       # Build firmware
idf.py flash       # Flash to device
idf.py monitor     # Monitor serial output
python scripts/release.py [board-name]  # Build for specific board
```

## Development Patterns

### Configuration Systems
- **mem0**: Environment-based config with Pydantic validation
- **xiaozhi-server**: Layered YAML configs with API overrides
- **xiaozhi-esp32**: CMake-based board selection with JSON configs

### Provider/Plugin Architectures
- **mem0**: Factory pattern for LLM/vector store providers
- **xiaozhi-server**: Plugin system for IoT functions and AI services
- **xiaozhi-esp32**: Board abstraction layer with inheritance hierarchy

### Memory and State Management
- **mem0**: SQLite history + vector embeddings with scoped sessions
- **xiaozhi-server**: Memory systems (local/mem0ai) + Redis caching
- **xiaozhi-esp32**: Device state management with MCP tools

## Key Architectural Concepts

### Multi-modal AI Pipeline
The xiaozhi ecosystem implements a complete voice AI pipeline:
1. **Wake Word** → **ASR** → **LLM** → **TTS** → **Audio Output**
2. **Vision** → **VLLM** → **Multimodal responses**
3. **Intent Recognition** → **Function Calling** → **IoT Control**

### Memory Layer Integration
- mem0 provides persistent memory across conversations
- Integration points in xiaozhi-server for personalized AI interactions
- Scoped memory by user_id, agent_id, or run_id

### Hardware Abstraction
- xiaozhi-esp32 supports 70+ boards through unified interfaces
- Audio codec abstraction (ES8311, ES8374, ES8388, etc.)
- Display driver abstraction (SPI LCD, I2C OLED)

## Testing Strategies

### mem0
- Unit tests with pytest in `tests/` directory
- Provider-specific test modules
- Mock implementations for external dependencies

### xiaozhi-server
- Performance testing tools for ASR/LLM/TTS
- Web-based audio testing via `test/test_page.html`
- Module-specific performance testers

### xiaozhi-esp32  
- Hardware-in-loop testing on actual devices
- Audio pipeline validation
- Board-specific functionality verification

## Database Systems

### xiaozhi-server Backend
- **Java API**: MySQL with MyBatis Plus, Liquibase migrations
- **Python Server**: SQLite for local data, Redis for caching
- **Memory Systems**: Vector databases + traditional SQL

### mem0
- SQLite for conversation history
- Vector stores for embeddings (configurable providers)
- Optional graph databases (Neo4j, Neptune)

## Security Considerations

- JWT authentication across all web services
- Shiro-based security in Java components
- Device token authentication for ESP32 connections
- API key management for AI services
- No hardcoded secrets in configuration files