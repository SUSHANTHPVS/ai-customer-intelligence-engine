# React Dashboard Frontend

Interactive dashboard for customer intelligence and revenue risk management.

## Tech Stack

- **Framework**: React 18 + Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Charting**: Recharts
- **Icons**: React Icons
- **Routing**: React Router

## Project Structure

```
frontend/
├── src/
│   ├── pages/              # Page components
│   │   ├── Dashboard.jsx   # Executive overview
│   │   ├── CustomerIntel.jsx
│   │   ├── ChurnAnalysis.jsx
│   │   ├── Marketing.jsx
│   │   └── Simulator.jsx
│   │
│   ├── components/         # Reusable components
│   │   ├── Header.jsx
│   │   ├── Sidebar.jsx
│   │   ├── MetricCard.jsx
│   │   ├── Chart.jsx
│   │   ├── CustomerTable.jsx
│   │   └── ScenarioBuilder.jsx
│   │
│   ├── hooks/              # Custom React hooks
│   │   ├── useCustomer.js
│   │   ├── usePredictions.js
│   │   └── useScenarios.js
│   │
│   ├── services/           # API calls
│   │   ├── api.js          # Axios instance
│   │   ├── predictions.js
│   │   ├── recommendations.js
│   │   └── customer.js
│   │
│   ├── context/            # Context providers
│   │   ├── AuthContext.jsx
│   │   └── ThemeContext.jsx
│   │
│   ├── App.jsx
│   ├── App.css
│   ├── index.css
│   └── main.jsx
│
├── public/
├── package.json
├── vite.config.js
├── tailwind.config.js
└── README.md
```

## Setup & Development

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Dashboard Pages

### 1. Executive Dashboard
- Key metrics (Revenue, Customers, Churn Rate, Retention)
- Revenue trend chart
- Customer growth
- Churn trend
- Alerts & notifications

### 2. Customer Intelligence
- Customer segments visualization
- Segment profiles
- Filters (Country, Industry, Plan, Acquisition Channel)
- Interactive segment comparison

### 3. Churn Analysis
- High-risk customers table
- Churn probability distribution
- Main churn drivers (SHAP)
- Risk scoring breakdown
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
