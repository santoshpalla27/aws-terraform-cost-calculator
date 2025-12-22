# AWS Cost Calculator Frontend - Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
```bash
# Copy environment template
cp env.example .env.local

# Edit .env.local with your API Gateway URL
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### 3. Run Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 📦 Production Deployment

### Option 1: Docker (Recommended)
```bash
# Build image
docker build -t aws-cost-calculator-frontend .

# Run container
docker run -p 3000:3000 \
  -e NEXT_PUBLIC_API_URL=http://your-api-gateway:8000 \
  -e NEXT_PUBLIC_WS_URL=ws://your-api-gateway:8000 \
  aws-cost-calculator-frontend
```

### Option 2: Docker Compose
```bash
# Update docker-compose.yml with your API URLs
docker-compose up -d
```

### Option 3: Node.js
```bash
npm run build
npm start
```

---

## 🧪 Testing the Frontend

### Without Backend (Mock Mode)
The frontend will show appropriate error states when the API is unavailable.

### With Backend
1. Start your API Gateway on port 8000
2. Update `.env.local` with the correct URLs
3. Test the upload flow:
   - Navigate to `/upload`
   - Upload a `.tf` file
   - Monitor job status
   - View cost results

---

## 📁 Project Structure

```
frontend/
├── app/                    # Next.js pages
│   ├── page.tsx           # Home page
│   ├── upload/            # Upload page
│   ├── jobs/              # Jobs list & detail
│   └── api/health/        # Health check
├── components/            # React components
│   ├── common/            # Shared UI
│   ├── upload/            # Upload form
│   ├── jobs/              # Job management
│   └── cost/              # Cost visualization
├── lib/                   # Core logic
│   ├── api/               # API client
│   ├── websocket/         # WebSocket service
│   ├── types/             # TypeScript types
│   └── utils/             # Utilities
└── Dockerfile             # Production build
```

---

## 🔧 Available Scripts

```bash
npm run dev      # Start development server
npm run build    # Build for production
npm start        # Start production server
npm run lint     # Run ESLint
```

---

## 🌐 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | API Gateway base URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000` |
| `NEXT_PUBLIC_MAX_FILE_SIZE` | Max upload size (bytes) | `52428800` (50MB) |

---

## 📖 Full Documentation

See [README.md](./README.md) for complete documentation.
