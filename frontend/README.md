# 📊 Customer Intelligence Dashboard

## Overview

A modern, real-time analytics dashboard built with **React + Vite + Tailwind CSS** that visualizes customer intelligence and machine learning model metrics. The dashboard integrates seamlessly with the Flask backend API to provide comprehensive insights into customer behavior, segmentation, and predictive analytics.

## 🎯 Features

### Analytics Dashboard
- **Customer Segmentation** - Pie chart visualization of customer segments
- **Engagement Metrics** - Bar charts showing customer engagement scores and trends
- **LTV Predictions** - Line charts comparing predicted vs. actual customer lifetime value
- **Churn Risk Analysis** - Table view of high-risk customers with actionable insights
- **Real-time Updates** - Auto-refresh and manual refresh capabilities

### Model Metrics Dashboard
- **Accuracy Tracking** - Real-time model accuracy percentage
- **Precision & Recall** - Detailed performance metrics for model evaluation
- **Performance History** - Line charts showing metric trends over time
- **Detailed Metrics Table** - Comprehensive view with status indicators
- **Trend Analysis** - Visual indicators showing metric direction (up/down/stable)

### UI/UX Features
- **Responsive Design** - Works on desktop, tablet, and mobile
- **Dark/Light Theme Ready** - Tailwind CSS with extensible theme support
- **Collapsible Sidebar** - Compact navigation for screen space optimization
- **Error Handling** - Graceful error messages and fallback UI
- **Health Status** - Real-time API connection status indicator
- **Loading States** - Smooth loading animations during data fetches

## 🛠️ Technology Stack

| Layer | Technology |
|-------|------------|
| **Framework** | React 18.2+ |
| **Build Tool** | Vite 5.1+ |
| **Styling** | Tailwind CSS 3.4+ |
| **State Management** | Zustand 4.4+ |
| **HTTP Client** | Axios 1.6+ |
| **Routing** | React Router DOM 6.20+ |
| **Charts** | Recharts 2.10+ |
| **Icons** | React Icons 4.12+ |

## 📁 Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── client.js          # API client with interceptors
│   ├── store/
│   │   └── dashboardStore.js  # Zustand store for state management
│   ├── components/
│   │   ├── AnalyticsDashboard.jsx      # Main analytics view
│   │   ├── ModelMetricsDashboard.jsx   # Model metrics view
│   │   └── HealthStatus.jsx            # API health indicator
│   ├── App.jsx                # Main app component
│   ├── main.jsx               # React entry point
│   ├── App.css                # Global styles
│   └── index.css              # Tailwind imports
├── public/                    # Static assets
├── Dockerfile                 # Multi-stage production build
├── docker-compose.yml         # Development setup (optional)
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # Tailwind CSS config
├── postcss.config.js         # PostCSS config
├── package.json              # Dependencies
└── README.md                 # This file
```

## 🚀 Getting Started

### Prerequisites
- Node.js 16+ and npm 8+
- Backend API running on http://localhost:5000
- Docker (for containerized deployment)

### Development Setup

1. **Install Dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Create Environment File** (optional)
   ```bash
   # .env or set VITE_API_URL environment variable
   VITE_API_URL=http://localhost:5000
   ```

3. **Start Development Server**
   ```bash
   npm run dev
   ```
   Dashboard available at http://localhost:5173

4. **Build for Production**
   ```bash
   npm run build
   ```
   Output in `dist/` directory

### Docker Deployment

1. **Build Docker Image**
   ```bash
   docker build -t customer-intelligence-frontend .
   ```

2. **Run Container**
   ```bash
   docker run -p 80:80 customer-intelligence-frontend
   ```

3. **Or Use Docker Compose**
   ```bash
   docker-compose up frontend
   ```

## 📡 API Integration

### API Client Configuration

The frontend uses an Axios-based API client (`src/api/client.js`) with:
- Base URL from `VITE_API_URL` environment variable
- Request/response interceptors
- Automatic authorization header injection
- Error handling with logout on 401

### Available Endpoints

```javascript
// Analytics
GET /analytics/customer-segmentation
GET /analytics/engagement-metrics
GET /analytics/ltv-predictions
GET /analytics/churn-risk

// Models
GET /models/metrics
GET /models/performance

// Health
GET /health
```

### State Management (Zustand)

```javascript
import useDashboardStore from './store/dashboardStore';

// In component
const { analytics, loading, error, fetchAnalytics } = useDashboardStore();

// Actions
await store.checkHealth();
await store.fetchAnalytics();
await store.fetchModelMetrics();
await store.refreshAll();
```

## 🎨 UI Components

### AnalyticsDashboard
- KPI cards with icons
- Customer segmentation pie chart
- Engagement metrics bar chart
- LTV predictions line chart
- Churn risk analysis table

### ModelMetricsDashboard
- Performance KPI cards
- Performance history line chart
- Detailed metrics table with status
- Trend indicators

### HealthStatus
- API connection status
- Visual health indicator
- Refresh button with loading state

## 🔧 Configuration

### Tailwind CSS
Customize theme in `tailwind.config.js`:
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        // Add custom colors
      }
    }
  }
}
```

### Vite Configuration
Edit `vite.config.js` to modify:
- Build output directory
- Dev server port and proxy
- Chunk splitting strategy
- Source maps and minification

### Environment Variables
- `VITE_API_URL` - Backend API base URL (default: http://localhost:5000)
- All vars must be prefixed with `VITE_` to be accessible in code

## 📊 Chart Components

The dashboard uses **Recharts** for visualizations:

### Pie Chart (Segmentation)
```jsx
<PieChart data={data}>
  <Pie dataKey="count" nameKey="segment" />
  <Tooltip />
</PieChart>
```

### Bar Chart (Engagement)
```jsx
<BarChart data={data}>
  <Bar dataKey="value" fill="#3B82F6" />
</BarChart>
```

### Line Chart (LTV & Performance)
```jsx
<LineChart data={data}>
  <Line dataKey="metric" stroke="#10B981" />
</LineChart>
```

## 🔐 Security Features

- ✅ JWT token support (stored in localStorage)
- ✅ Automatic token injection in headers
- ✅ 401 error handling with logout
- ✅ CORS-enabled for cross-origin requests
- ✅ Request timeout configuration
- ✅ Error boundary support

## 📱 Responsive Design

Built with **Tailwind CSS** breakpoints:
- **Mobile** (default): Full-width, stacked layout
- **Tablet** (`md:`): 2-column grids
- **Desktop** (`lg:`): Full multi-column layout
- **Wide** (`xl:`): Optimized spacing and typography

## 🚨 Error Handling

The dashboard handles various error scenarios:
- API connection failures
- Network timeouts
- Invalid responses
- 401/403 authorization errors
- Data loading errors

Error messages display in banner with dismiss button.

## ⚡ Performance Optimizations

- **Code Splitting**: Separate chunks for vendors (React, Charts, UI)
- **Lazy Loading**: Components load on-demand
- **Minification**: Terser for optimal bundle size
- **Tree Shaking**: Unused code removal
- **Source Maps**: Development debugging support

## 🧪 Development Tips

### Debug API Calls
```javascript
// In browser console
const store = useDashboardStore.getState();
console.log(store.analytics);
```

### Test with Mock Data
Modify API client to return mock data:
```javascript
const mockData = { /* ... */ };
return Promise.resolve({ data: mockData });
```

### Monitor Performance
```bash
npm run build  # Check bundle size
docker build -t dashboard . --progress=plain
```

## 📚 Additional Resources

- [React Documentation](https://react.dev)
- [Vite Guide](https://vitejs.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [Zustand](https://github.com/pmndrs/zustand)
- [Recharts](https://recharts.org)
- [Axios](https://axios-http.com)

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/new-feature`
2. Make changes and test
3. Commit: `git commit -am 'Add feature'`
4. Push: `git push origin feature/new-feature`
5. Create Pull Request

## 📝 License

This project is part of the AI Customer Intelligence Engine ecosystem.

## 🆘 Support

For issues and questions:
1. Check [DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md)
2. Review API documentation
3. Check browser console for errors
4. Verify backend connectivity
5. Check `.env` configuration

---

**Last Updated**: 2024-01-15  
**Version**: 1.0.0
- Recommended interventions

### 4. Marketing Analytics
- Campaign performance metrics
- Channel comparison (CAC, ROAS, LTV:CAC)
- Campaign attribution
- Conversion funnel
- Customer acquisition trends

### 5. What-if Simulator
- Interactive sliders:
  - Churn reduction rate
  - Retention campaign effectiveness
  - Discount percentage
- Real-time calculations:
  - Customers retained
  - Revenue preserved
  - Estimated ROI

## API Integration

All API calls go through `/services/api.js`:

```javascript
// Example
import { getPrediction } from './services/predictions';

const data = await getPrediction(customerId);
```

Environment variables:

```
VITE_API_URL=http://localhost:8000
```

## Styling

Using Tailwind CSS for all styling. Custom components use utility classes.

## State Management

Using Zustand for lightweight state management:

```javascript
import { create } from 'zustand';

const useStore = create((set) => ({
  customers: [],
  setCustomers: (customers) => set({ customers }),
}));
```

## Deployment

- **Vercel**: Automatic deployment from GitHub
- **Netlify**: Alternative option
- **Docker**: See project root `/Dockerfile`

## Environment Setup

```bash
# .env.local
VITE_API_URL=http://localhost:8000
VITE_DEBUG=true
```

## Performance Optimization

- Code splitting with React.lazy
- Image optimization
- Memoization of heavy components
- Debouncing of API calls

## Accessibility

- ARIA labels
- Keyboard navigation
- Color contrast compliance
- Semantic HTML

## Testing (To Be Added)

- Unit tests with Vitest
- Component tests with React Testing Library
- E2E tests with Playwright
