# Ollama Agent Framework Chat with MCP Integration

로컬 LLM(Ollama)과 Microsoft Agent Framework, 그리고 Model Context Protocol(MCP)을 활용한 웹 기반 AI 채팅 애플리케이션입니다.

## 주요 기능

- **로컬 LLM**: Ollama를 통한 완전한 로컬 실행 (프라이버시 보장)
- **Agent Framework**: Microsoft Agent Framework를 사용한 고급 에이전트 기능
- **MCP 지원**: Model Context Protocol을 통한 확장 가능한 툴 시스템
- **실시간 스트리밍**: Server-Sent Events를 통한 실시간 응답
- **웹 UI**: 직관적인 채팅 인터페이스
- **⚡ TTFT 최적화**: 빠른 첫 응답 시간 (< 500ms)

## 사전 준비

### 1. Ollama 설치 및 설정

```bash
# Ollama 다운로드 및 설치
# https://ollama.com에서 다운로드

# Ollama 서버 실행
ollama serve

# 모델 다운로드 (다른 터미널에서)
ollama pull mistral
```

**추천 모델:**
- `mistral` - 균형잡힌 성능
- `llama3.2` - 최신 모델
- `phi3` - 가벼운 모델

### 2. Python 환경

- Python 3.10 이상
- pip 패키지 매니저

### 3. Node.js (MCP 서버용, 선택사항)

- Node.js 18 이상 (MCP 서버 사용 시)
- npx 명령어 사용 가능

## 설치 및 실행

### 1. 저장소 클론 (또는 다운로드)

```bash
cd agent-framework
```

### 2. 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일이 이미 생성되어 있습니다. 필요시 수정:

```env
# Ollama 설정
OLLAMA_ENDPOINT=http://localhost:11434/v1/
# 주의: 모델은 웹 UI에서 선택합니다

# 서버 설정
HOST=0.0.0.0
PORT=8000

# MCP 설정
MCP_CONFIG_PATH=./config/mcp_servers.yaml
MCP_LOG_LEVEL=INFO
```

### 4. 애플리케이션 실행

```bash
# backend 폴더에서 실행
python app.py
```

또는:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 5. 브라우저에서 접속 및 모델 선택

1. **브라우저로 접속**: http://localhost:8000
2. **모델 선택**: 상단 헤더의 모델 선택 드롭다운 클릭
3. **모델 로드**: 원하는 모델의 "Load Model" 버튼 클릭
4. **채팅 시작**: 모델 로드 완료 후 메시지 입력

**추가 페이지:**
- **MCP 설정**: http://localhost:8000/mcp-settings

## 프로젝트 구조

```
agent-framework/
├── backend/                    # 백엔드 애플리케이션
│   ├── app.py                 # FastAPI 메인 앱
│   ├── agents/                # Agent Framework 에이전트
│   ├── mcp/                   # MCP 관리자
│   ├── routers/               # API 라우터
│   ├── services/              # 서비스 (Ollama 등)
│   ├── models/                # 데이터 모델
│   └── requirements.txt       # Python 의존성
│
├── frontend/                  # 프론트엔드
│   ├── static/               # 정적 파일 (CSS, JS)
│   └── templates/            # HTML 템플릿
│
├── config/                    # 설정 파일
│   ├── .env.example          # 환경변수 예시
│   └── mcp_servers.yaml      # MCP 서버 설정
│
├── DESIGN.md                  # 설계 문서
└── README.md                  # 이 파일
```

## API 엔드포인트

### 채팅 API

- `POST /api/chat/message` - 일반 메시지 전송 (비스트리밍)
- `POST /api/chat/stream` - 스트리밍 메시지 전송 (SSE)
- `GET /api/chat/health` - 서버 상태 확인
- `GET /api/chat/models` - 사용 가능한 모델 목록

### MCP API

- `GET /api/mcp/servers` - MCP 서버 목록
- `GET /api/mcp/tools` - 사용 가능한 툴 목록
- `POST /api/mcp/servers/{name}/toggle` - 서버 활성화/비활성화
- `POST /api/mcp/test/{name}` - 서버 연결 테스트

## MCP 서버 설정

MCP 서버를 추가하려면 `config/mcp_servers.yaml` 파일을 편집하세요:

```yaml
mcp_servers:
  - name: "filesystem"
    type: "stdio"
    enabled: true
    description: "파일 시스템 접근"
    config:
      command: "npx"
      args:
        - "-y"
        - "@modelcontextprotocol/server-filesystem"
        - "/allowed/directory/path"
    env: {}
```

**사용 가능한 MCP 서버:**

1. **Filesystem** - 파일 읽기/쓰기
   ```bash
   npx -y @modelcontextprotocol/server-filesystem
   ```

2. **GitHub** - GitHub API 통합
   ```bash
   npx -y @modelcontextprotocol/server-github
   ```
   환경변수: `GITHUB_TOKEN` 필요

3. **SQLite** - 데이터베이스 쿼리
   ```bash
   npx -y @modelcontextprotocol/server-sqlite
   ```

## ⚡ TTFT 최적화

이 프로젝트는 **Time to First Token (첫 토큰까지의 시간)** 최적화에 중점을 두었습니다.

### 구현된 최적화 기법

1. **Connection Pooling**: HTTP 연결 재사용으로 지연 시간 감소
2. **Model Preloading**: 서버 시작 시 모델을 메모리에 미리 로드
3. **Agent Warmup**: 에이전트 파이프라인 사전 초기화
4. **Lazy Initialization**: 필요할 때만 리소스 초기화
5. **Optimized Prompts**: 짧고 효율적인 시스템 프롬프트
6. **Streaming Optimization**: 버퍼링 제거 및 즉각적 피드백

### 성능 지표

- **Cold Start TTFT**: ~2초
- **Warm TTFT**: ~400-500ms
- **일반 요청**: ~350-450ms

자세한 내용은 [TTFT_OPTIMIZATION.md](TTFT_OPTIMIZATION.md) 참고

---

## 사용 예시

### 기본 대화

```
User: 안녕하세요!
Agent: 안녕하세요! 무엇을 도와드릴까요?
```

### 내장 도구 사용

```
User: 서울 날씨 알려줘
Agent: [🔧 Using: get_weather]
      서울의 날씨는 맑음이며 최고 기온은 23°C입니다.
```

```
User: 125 * 48 계산해줘
Agent: [🔧 Using: calculate]
      Result: 6000
```

### MCP 툴 사용 (Phase 2)

```
User: 프로젝트의 README.md 파일 읽어줘
Agent: [🔧 Using: filesystem/read]
      파일 내용: ...
```

## 문제 해결

### Ollama 연결 실패

```bash
# Ollama가 실행 중인지 확인
ollama serve

# 다른 터미널에서 모델 확인
ollama list
```

### 포트 충돌

`.env` 파일에서 포트 변경:
```env
PORT=8001
```

### MCP 서버 오류

- Node.js가 설치되어 있는지 확인
- `npx` 명령어가 작동하는지 확인
- MCP 서버가 활성화되어 있는지 확인 (`enabled: true`)

## 개발 로드맵

### Phase 1 (완료)
- ✅ 기본 채팅 기능
- ✅ Ollama 통합
- ✅ 스트리밍 응답
- ✅ 웹 UI
- ✅ MCP 기본 구조

### Phase 2 (예정)
- 🔧 MCP 서버 실제 통합
- 🔧 동적 MCP 서버 관리
- 🔧 툴 호출 로깅
- 🔧 대화 히스토리 저장

### Phase 3 (예정)
- 🎨 커스텀 MCP 서버 개발 도구
- 🎨 멀티모달 지원
- 🎨 A2A (Agent-to-Agent) 통신
- 🎨 고급 UI 기능

## 기여

이슈 및 풀 리퀘스트 환영합니다!

## 라이선스

MIT License

## 참고 자료

- [Microsoft Agent Framework](https://github.com/microsoft/agent-framework)
- [Ollama](https://ollama.com)
- [Model Context Protocol](https://modelcontextprotocol.io)
- [FastAPI](https://fastapi.tiangolo.com)

## 문의

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.
