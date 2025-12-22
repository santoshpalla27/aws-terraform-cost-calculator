# AWS Cost Calculator - Frontend

Production-grade Next.js frontend for the Terraform-based AWS Cost Calculator platform.

## Overview

This is a **pure UI layer** that communicates exclusively with the API Gateway. It does NOT:
- Run Terraform
- Calculate costs
- Contain business logic
- Store secrets
- Call AWS APIs directly

## Features

- 📤 **Terraform File Upload** - Drag-and-drop interface with validation
- 📊 **Cost Visualization** - Detailed breakdowns by service and resource
- 🔄 **Real-time Updates** - WebSocket integration for job status
- 📈 **Confidence Scores** - Visual indicators for estimate accuracy
- ⚠️ **Warnings & Assumptions** - Transparent cost calculation details
- 🎨 **Modern UI** - Built with Tailwind CSS and Lucide icons

## Tech Stack

- **Framework**: Next.js 15 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Icons**: Lucide React
- **Charts**: Recharts

## Getting Started

### Prerequisites

- Node.js 20+
- npm or yarn

### Local Development

1. **Clone and navigate to the frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   
   Copy `env.example` to `.env.local`:
   ```bash
   cp env.example .env.local
   ```
   
   Update the values:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   NEXT_PUBLIC_WS_URL=ws://localhost:8000
   NEXT_PUBLIC_MAX_FILE_SIZE=52428800
   ```

4. **Run development server**
   ```bash
   npm run dev
   ```
   
   Open [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

## Docker Deployment

### Build Docker Image

```bash
docker build -t aws-cost-calculator-frontend .
```

### Run with Docker Compose

```bash
docker-compose up -d
```

The frontend will be available at `http://localhost:3000`

### Environment Variables for Docker

Create a `.env` file:
```env
NEXT_PUBLIC_API_URL=http://api-gateway:8000
NEXT_PUBLIC_WS_URL=ws://api-gateway:8000
```

## Project Structure

```
frontend/
├── app/                    # Next.js App Router
│   ├── layout.tsx         # Root layout with navigation
│   ├── page.tsx           # Home page
│   ├── upload/            # Upload page
│   ├── jobs/              # Jobs list and detail pages
│   └── globals.css        # Global styles
├── components/
│   ├── common/            # Shared components (loading, error, empty states)
│   ├── upload/            # Upload form component
│   ├── jobs/              # Job list and status components
│   └── cost/              # Cost visualization components
├── lib/
│   ├── api/               # API client
│   ├── websocket/         # WebSocket service
│   ├── types/             # TypeScript definitions
│   └── utils/             # Utility functions
├── Dockerfile             # Production Docker build
├── docker-compose.yml     # Docker Compose configuration
└── next.config.ts         # Next.js configuration
```

## API Integration

The frontend expects the following API endpoints:

### Job Management
- `POST /api/jobs` - Create new cost estimation job
- `GET /api/jobs` - List all jobs (with pagination)
- `GET /api/jobs/:id` - Get job details
- `GET /api/jobs/:id/results` - Get cost estimation results
- `POST /api/jobs/:id/retry` - Retry failed job

### Usage Profiles
- `GET /api/usage-profiles` - Get available usage profiles
- `GET /api/usage-profiles/:id` - Get specific profile

### WebSocket
- `WS /api/jobs/:id/status` - Real-time job status updates

## Key Components

### Upload Form (`components/upload/upload-form.tsx`)
- Drag-and-drop file upload
- Client-side validation (.tf, .tfvars, .zip)
- Progress tracking
- Usage profile selection

### Job List (`components/jobs/job-list.tsx`)
- Paginated job list
- Status filtering
- Real-time status badges

### Job Status (`components/jobs/job-status.tsx`)
- WebSocket integration for live updates
- Progress tracking
- Retry functionality for failed jobs

### Cost Summary (`components/cost/cost-summary.tsx`)
- Total monthly cost display
- Confidence score visualization
- Service breakdown charts
- Warnings and assumptions

### Resource Breakdown (`components/cost/resource-breakdown.tsx`)
- Detailed cost table
- Per-resource confidence scores
- Cost component breakdown
- Assumptions and warnings popover

## Development Guidelines

### Adding New Features

1. Create types in `lib/types/index.ts`
2. Add API methods in `lib/api/api-client.ts`
3. Build components in appropriate directories
4. Create pages in `app/` directory

### Styling

- Use Tailwind CSS utility classes
- Follow the existing color scheme (blue primary)
- Ensure responsive design (mobile-first)
- Use the `cn()` utility for conditional classes

### Type Safety

- All API responses must be typed
- Use TypeScript strict mode
- Avoid `any` types
- Export types from `lib/types/index.ts`

## Troubleshooting

### WebSocket Connection Issues

If WebSocket connections fail, the app will gracefully degrade. Consider implementing polling as a fallback:

```typescript
// In components/jobs/job-status.tsx
// Add polling logic if WebSocket fails
```

### API Connection Errors

Check that `NEXT_PUBLIC_API_URL` is correctly set and the API Gateway is running.

### Build Errors

Ensure all dependencies are installed:
```bash
rm -rf node_modules package-lock.json
npm install
```

## Production Checklist

- [ ] Set production API URLs in environment variables
- [ ] Enable HTTPS for API communication
- [ ] Configure CORS on API Gateway
- [ ] Set up error monitoring (e.g., Sentry)
- [ ] Enable rate limiting
- [ ] Add authentication if required
- [ ] Test WebSocket connectivity
- [ ] Verify file upload limits
- [ ] Test responsive design on mobile devices

## License

Part of the AWS Cost Calculator platform.
