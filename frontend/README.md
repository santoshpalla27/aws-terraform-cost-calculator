# Terraform Cost Estimator - Frontend

Production-grade React + TypeScript UI for Terraform cost estimation.

## Features

- **File Upload**: Drag & drop or browse for Terraform plan JSON
- **Job Progress**: 5-stage progress indicator with animations
- **Cost Visualizations**:
  - Service breakdown (Pie chart)
  - Region breakdown (Bar chart)
  - Resource list (Sortable table)
- **Confidence Indicators**: Visual confidence scoring
- **Accessible Design**: ARIA labels, keyboard navigation
- **Responsive**: Works on desktop and tablet

## Quick Start

```bash
cd frontend
npm install
npm run dev
```

Visit: http://localhost:3000

## Build for Production

```bash
npm run build
```

## Project Structure

```
src/
├── components/
│   ├── FileUpload/
│   │   ├── FileUpload.tsx
│   │   └── FileUpload.css
│   ├── JobProgress/
│   │   ├── JobProgress.tsx
│   │   └── JobProgress.css
│   ├── ConfidenceIndicator/
│   │   ├── ConfidenceIndicator.tsx
│   │   └── ConfidenceIndicator.css
│   └── CostDashboard/
│       ├── CostDashboard.tsx
│       ├── ServiceChart.tsx
│       ├── RegionChart.tsx
│       ├── ResourceList.tsx
│       └── *.css
├── services/
│   ├── api.ts
│   └── types.ts
├── App.tsx
└── main.tsx
```

## Components

### FileUpload
- Drag & drop support
- File type validation
- Keyboard accessible

### JobProgress
- 5 stages: Parsing → Enriching → Modeling → Calculating → Complete
- Progress bar with percentage
- Animated icons

### CostDashboard
- Total cost summary
- Confidence indicator
- Service/Region charts
- Resource table

### Charts
- **ServiceChart**: Pie chart using Recharts
- **RegionChart**: Bar chart using Recharts
- Responsive containers
- Tooltips and legends

## API Integration

All backend APIs are integrated via `services/api.ts`:

- Plan Parser: `/api/v1/parse`
- Metadata Resolver: `/api/v1/enrich`
- Usage Modeling: `/api/v1/scenarios`
- Cost Aggregation: `/api/v1/estimate`
- Results Storage: `/api/v1/store`, `/api/v1/jobs/*`

## Accessibility

- ARIA labels on all interactive elements
- Keyboard navigation support
- Screen reader compatible
- Color contrast: WCAG AA compliant

## Technologies

- React 18
- TypeScript 5
- Vite (build tool)
- Recharts (charts)
- Axios (HTTP client)

## License

[Your License]
