# 프로젝트 설계안: Ollama + MS Agent Framework + MCP 통합 Web UI Chat

## 📋 프로젝트 개요
Microsoft Agent Framework, Ollama 로컬 LLM, 그리고 MCP(Model Context Protocol)를 활용한 확장 가능한 웹 채팅 애플리케이션

---

## 🏗️ 아키텍처 구조

```
agent-framework/
├── backend/
│   ├── app.py                      # FastAPI 메인 애플리케이션
│   ├── agents/
│   │   ├── __init__.py
│   │   └── chat_agent.py           # Agent Framework 기반 채팅 에이전트
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── mcp_manager.py          # MCP 서버 관리자
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── stdio_tool.py       # 로컬 MCP 서버 (파일시스템, 계산기 등)
│   │   │   ├── http_tool.py        # HTTP/SSE MCP 서버
│   │   │   └── websocket_tool.py   # WebSocket MCP 서버
│   │   └── servers/
│   │       ├── filesystem.json     # 파일시스템 MCP 서버 설정
│   │       ├── github.json         # GitHub MCP 서버 설정
│   │       └── custom.json         # 커스텀 MCP 서버 설정
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── chat.py                 # 채팅 API 엔드포인트
│   │   └── mcp.py                  # MCP 관리 API
│   ├── services/
│   │   ├── __init__.py
│   │   └── ollama_service.py       # Ollama 연결 서비스
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py              # Pydantic 모델
│   └── requirements.txt
│
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   ├── style.css           # 메인 스타일
│   │   │   └── components.css      # 컴포넌트 스타일
│   │   └── js/
│   │       ├── chat.js             # 채팅 로직
│   │       ├── mcp-manager.js      # MCP 서버 관리 UI
│   │       └── utils.js            # 유틸리티 함수
│   └── templates/
│       ├── index.html              # 메인 채팅 UI
│       └── mcp-settings.html       # MCP 설정 UI
│
├── config/
│   ├── .env.example                # 환경변수 예시
│   └── mcp_servers.yaml            # MCP 서버 설정 파일
│
├── mcp_servers/                    # 커스텀 MCP 서버 (선택사항)
│   └── custom_tools/
│       └── example_server.py       # 커스텀 MCP 서버 예시
│
└── README.md
```

---

## 🔧 기술 스택

### Backend
- `agent-framework` - Microsoft Agent Framework (MCP 지원)
- `FastAPI` - 비동기 웹 프레임워크
- `uvicorn` - ASGI 서버
- `python-dotenv` - 환경변수 관리
- `pyyaml` - MCP 서버 설정 파일 파싱
- `websockets` - WebSocket MCP 서버용
- `httpx` - HTTP MCP 서버용

### Frontend
- Vanilla JavaScript
- HTML5 + CSS3
- Server-Sent Events (SSE) - 스트리밍 응답
- WebSocket (MCP 실시간 연결용)

### LLM
- Ollama (로컬 실행)
- 추천 모델: `mistral`, `llama3.2`, `phi3`

### MCP Ecosystem
- `@modelcontextprotocol/server-filesystem` - 파일 시스템 접근
- `@modelcontextprotocol/server-github` - GitHub 통합
- 커스텀 MCP 서버 (필요시 개발)

---

## 🎯 MCP 통합 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                         Web UI                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Chat UI      │  │ MCP Settings │  │ Tool Monitor │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/SSE/WebSocket
┌────────────────────────▼────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Agent Framework + Ollama                   │  │
│  │  ┌─────────────┐         ┌──────────────┐           │  │
│  │  │ Chat Agent  │◄────────┤ MCP Manager  │           │  │
│  │  └─────────────┘         └──────┬───────┘           │  │
│  │                                  │                    │  │
│  └──────────────────────────────────┼────────────────────┘  │
│                                     │                       │
│  ┌──────────────────────────────────▼────────────────────┐ │
│  │              MCP Tool Adapters                        │ │
│  │  ┌─────────┐  ┌─────────┐  ┌──────────┐             │ │
│  │  │  Stdio  │  │  HTTP   │  │WebSocket │             │ │
│  │  └────┬────┘  └────┬────┘  └─────┬────┘             │ │
│  └───────┼────────────┼─────────────┼───────────────────┘ │
└──────────┼────────────┼─────────────┼──────────────────────┘
           │            │             │
┌──────────▼────┐  ┌───▼─────┐  ┌────▼─────┐
│ Local MCP     │  │ Remote  │  │ Real-time│
│ Servers       │  │ MCP API │  │ MCP WS   │
│               │  │         │  │          │
│ • Filesystem  │  │ • GitHub│  │ • Custom │
│ • Calculator  │  │ • Search│  │ • DB     │
│ • SQLite      │  │ • APIs  │  │ • Notify │
└───────────────┘  └─────────┘  └──────────┘
```

---

## 📊 주요 컴포넌트

### 1. MCP Manager (`mcp/mcp_manager.py`)
- MCP 서버 동적 로딩/언로딩
- 서버 상태 모니터링
- 툴 디스커버리 (자동 인식)
- 연결 타입별 어댑터 관리 (Stdio/HTTP/WebSocket)
- 에러 핸들링 및 재연결 로직

### 2. MCP Tool Adapters (`mcp/tools/`)
- **MCPStdioTool**: 로컬 프로세스 기반 MCP 서버
- **MCPStreamableHTTPTool**: HTTP + SSE 기반 원격 MCP 서버
- **MCPWebsocketTool**: 실시간 양방향 통신

### 3. Backend - Enhanced Agent (`agents/chat_agent.py`)
- Ollama 기반 LLM 연결
- MCP 툴 자동 등록
- 대화 컨텍스트 관리
- 툴 호출 로깅
- 스트리밍 응답 지원

### 4. Backend - Chat API (`routers/chat.py`)
```
POST /api/chat/message      # 일반 메시지 (비스트리밍)
GET  /api/chat/stream       # 스트리밍 메시지 (SSE)
GET  /api/health            # Ollama 연결 상태 확인
GET  /api/models            # 사용 가능한 모델 목록
```

### 5. Backend - MCP API (`routers/mcp.py`)
```
GET  /api/mcp/servers          # 등록된 MCP 서버 목록
POST /api/mcp/servers          # 새 MCP 서버 추가
DELETE /api/mcp/servers/{id}   # MCP 서버 제거
GET  /api/mcp/tools            # 사용 가능한 모든 툴 목록
POST /api/mcp/test/{server_id} # MCP 서버 연결 테스트
```

---

## 🔄 데이터 플로우

```
[User: "GitHub에서 issue 검색해줘"]
    ↓
[Frontend] → POST /api/chat/stream
    ↓
[Chat Agent]
    ↓ (분석: GitHub 툴 필요)
[MCP Manager] → GitHub MCP Server
    ↓
[GitHub API 호출]
    ↓
[결과 수집]
    ↓
[Agent가 결과 해석]
    ↓
[Stream Response] → Frontend
    ↓
[UI 업데이트: "issue 5개 발견..."]
```

---

## 🛠️ 핵심 기능

### Phase 1 - 기본 채팅 + MCP 기초
- ✅ Ollama 기반 채팅
- ✅ 스트리밍 응답
- ✅ 기본 MCP 서버 1~2개 (파일시스템, 계산기)
- ✅ MCP 툴 자동 인식
- ✅ 툴 호출 표시

### Phase 2 - MCP 확장
- 🔧 다중 MCP 서버 관리
- 🔧 GitHub MCP 통합
- 🔧 SQLite MCP 통합
- 🔧 웹 검색 MCP 통합
- 🔧 MCP 서버 동적 추가/제거 UI
- 🔧 툴 호출 로그 및 디버깅

### Phase 3 - 고급 기능
- 🎨 커스텀 MCP 서버 개발 템플릿
- 🎨 툴 체인 실행 (여러 툴 순차 실행)
- 🎨 대화 히스토리 저장 (DB)
- 🎨 멀티모달 지원 (이미지 처리 MCP)
- 🎨 에이전트 간 통신 (A2A)

---

## ⚙️ 환경 설정

### .env 파일
```env
# Ollama 설정
OLLAMA_ENDPOINT=http://localhost:11434/v1/
OLLAMA_MODEL=mistral

# 서버 설정
HOST=0.0.0.0
PORT=8000

# MCP 설정
MCP_CONFIG_PATH=./config/mcp_servers.yaml
MCP_LOG_LEVEL=INFO
```

### mcp_servers.yaml
```yaml
mcp_servers:
  - name: "filesystem"
    type: "stdio"
    enabled: true
    config:
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]

  - name: "github"
    type: "stdio"
    enabled: true
    config:
      command: "npx"
      args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "your-token-here"

  - name: "custom-api"
    type: "http"
    enabled: false
    config:
      url: "https://api.example.com/mcp"
      headers:
        Authorization: "Bearer YOUR_TOKEN"
```

---

## 📦 주요 의존성 (requirements.txt)

```txt
# Core Framework
agent-framework>=0.1.0

# Web Framework
fastapi>=0.115.0
uvicorn[standard]>=0.32.0
python-multipart>=0.0.12

# MCP Support
websockets>=14.0
httpx>=0.28.0
pyyaml>=6.0

# Utilities
python-dotenv>=1.0.0
pydantic>=2.10.0
pydantic-settings>=2.6.0
```

---

## 🚀 실행 방법

```bash
# 1. Ollama 설치 및 모델 다운로드
ollama pull mistral

# 2. 의존성 설치
pip install -r backend/requirements.txt

# 3. 환경 변수 설정
cp config/.env.example .env
# .env 파일 편집

# 4. MCP 서버 설정
cp config/mcp_servers.yaml.example config/mcp_servers.yaml
# mcp_servers.yaml 파일 편집

# 5. Ollama 실행
ollama serve

# 6. 애플리케이션 실행
cd backend
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 7. 브라우저 접속
# Chat UI: http://localhost:8000
# MCP Settings: http://localhost:8000/mcp-settings
```

---

## 🎨 UI 구성

### 메인 채팅 화면
```
┌─────────────────────────────────────────────┐
│  🤖 Ollama Agent Chat          [⚙️ MCP]    │
├─────────────────────────────────────────────┤
│                                             │
│  User: GitHub issue 검색해줘                │
│                                             │
│  Agent: [🔧 Using: GitHub Search Tool]     │
│         찾은 issue:                         │
│         1. Bug fix needed #123              │
│         2. Feature request #124             │
│         ...                                 │
│                                             │
├─────────────────────────────────────────────┤
│  [Type message...]              [Send] [🎙️] │
└─────────────────────────────────────────────┘
│ Active Tools: 🗂️ Filesystem | 🐙 GitHub    │
└─────────────────────────────────────────────┘
```

---

## 🎯 MCP 서버 활용 시나리오

### 1. 파일시스템 MCP
- "프로젝트의 README.md 읽어줘"
- "새 파일 create_user.py 만들어줘"

### 2. GitHub MCP
- "microsoft/agent-framework의 최근 issue 보여줘"
- "내 저장소에 새 issue 생성해줘"

### 3. SQLite MCP
- "users 테이블에서 최근 가입자 10명 조회"
- "데이터베이스 스키마 보여줘"

### 4. 커스텀 API MCP
- 사내 API 연동
- 특정 서비스 통합

---

## 📝 MCP 통합의 장점

### 확장성
- ✅ 새로운 기능을 MCP 서버로 쉽게 추가
- ✅ 코드 수정 없이 툴 확장
- ✅ 표준 프로토콜로 재사용성 높음

### 유연성
- ✅ 로컬/원격 서버 혼합 사용
- ✅ 동적 서버 추가/제거
- ✅ 다양한 연결 타입 지원

### 보안
- ✅ 샌드박스 실행 (stdio)
- ✅ 인증 지원 (HTTP/WebSocket)
- ✅ 접근 권한 제어

---

## 구현 우선순위

### 현재 구현 (Phase 1)
1. 기본 FastAPI 서버 설정
2. Ollama 연결 및 기본 채팅
3. 간단한 Web UI (스트리밍 지원)
4. MCP Manager 기본 구조
5. 파일시스템 MCP 서버 통합 (1개)

### 다음 단계 (Phase 2)
- 추가 MCP 서버 통합
- MCP 관리 UI
- 고급 에러 핸들링
