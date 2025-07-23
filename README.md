# Financial Bubble Detection Dashboard

A sophisticated web application for visualizing and analyzing financial bubble estimates using options data. This dashboard provides interactive time-series visualizations of bubble probability estimates across different time horizons (tau groups) for major stocks and indices.

## 🎯 Overview

This research dashboard implements a financial bubble detection methodology that analyzes options market data to estimate the probability of asset price bubbles. The system processes put and call options data to generate bubble estimates with confidence intervals across multiple time horizons.

### Key Features

- **Interactive Time-Series Visualization**: Dynamic charts showing bubble estimates over time
- **Multi-Asset Analysis**: Support for 26 major stocks and indices (SPX, AAPL, TSLA, etc.)
- **Tau Group Analysis**: Three different time horizon groups for bubble detection
- **Options Data Integration**: Separate analysis for put options, call options, and combined estimates
- **Confidence Intervals**: Statistical bounds (upper/lower) for all bubble estimates
- **Date Range Filtering**: Customizable time period selection
- **Responsive Design**: Modern UI with dark/light theme support

## 📊 Methodology

### Bubble Estimates

The dashboard displays bubble probability estimates with three key components:

- **μ (mu)**: Point estimate of bubble probability
- **lb**: Lower bound of confidence interval
- **ub**: Upper bound of confidence interval

### Tau Groups

Three time horizon groups are analyzed:

- **Tau Group 1** (τ ≈ 0.25): Short-term bubble detection
- **Tau Group 2** (τ ≈ 0.5): Medium-term bubble detection
- **Tau Group 3** (τ ≈ 1.0): Long-term bubble detection

### Data Sources

- **Stock Price Data**: Split-adjusted historical prices (1996-2023)
- **Options Data**: Put and call options with various expiration dates
- **Time Series**: Daily bubble estimates with rolling window analysis

## 🚀 Getting Started

### Prerequisites

- [Bun](https://bun.sh/) runtime
- Node.js 18+ (alternative to Bun)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd financial-bubble-detection-dashboard
   ```

2. **Install dependencies**

   ```bash
   bun install
   ```

3. **Start the development server**

   ```bash
   bun run start
   ```

   The application will be available at `http://localhost:3000`

### Alternative with npm/yarn

```bash
npm install
npm run start
```

## 🏗️ Building for Production

```bash
bun run build
```

This creates an optimized production build in the `dist/` directory.

## 📁 Project Structure

```
src/
├── components/          # React components
│   ├── Dashboard.tsx    # Main dashboard component
│   ├── BubbleChart.tsx  # Interactive chart component
│   └── ui/             # Reusable UI components
├── hooks/              # Custom React hooks
│   └── useDashboardData.ts
├── types/              # TypeScript type definitions
│   └── bubbleData.ts   # Data structure interfaces
├── utils/              # Utility functions
│   └── dataLoader.ts   # Data fetching and processing
└── styles/             # CSS and styling
```

## 📈 Available Stocks

The dashboard supports analysis for the following assets:

- **Indices**: SPX (S&P 500)
- **Technology**: AAPL, MSFT, GOOG, AMZN, NVDA, INTC, CSCO, AMD
- **Financial**: JPM, BAC, C, WFC, MS, AIG
- **Other Sectors**: TSLA, F, GM, DIS, BA, GE, XOM, T, BABA, TWTR

## 🎨 Features

### Interactive Charts

- **Zoom & Pan**: Mouse wheel zoom, click-and-drag panning
- **Time Range Selection**: Slider controls for custom date ranges
- **Tooltip Details**: Hover for detailed bubble estimates and confidence intervals
- **Multi-Series Display**: Simultaneous visualization of all tau groups and stock prices

### Data Management

- **Cloud Storage**: Vercel Blob Storage for production data hosting
- **Local Fallback**: Development support with local JSON files
- **Efficient Loading**: Optimized data fetching with error handling

### User Interface

- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Theme Support**: Light and dark mode toggle
- **Loading States**: Smooth loading indicators and error handling
- **Accessibility**: ARIA labels and keyboard navigation support

## 🔧 Development

### Testing

```bash
bun run test
```

### Linting & Formatting

```bash
bun run lint      # Check code quality
bun run format    # Format code
bun run check     # Run both lint and format
```

### Data Management Scripts

```bash
bun run upload-data    # Upload JSON files to Vercel Blob Storage
bun run get-blob-urls  # Retrieve current blob URLs
bun run test-blob      # Test blob storage connectivity
```

## 🛠️ Technology Stack

- **Frontend Framework**: React 19 with TypeScript
- **Routing**: TanStack Router
- **Charts**: ECharts (via echarts-for-react)
- **Styling**: Tailwind CSS
- **UI Components**: Radix UI primitives
- **Build Tool**: Vite
- **Testing**: Vitest
- **Code Quality**: Biome (linting & formatting)
- **Data Storage**: Vercel Blob Storage

## 📊 Data Format

The application expects JSON data files with the following structure:

```typescript
interface BubbleData {
  metadata: {
    stockcode: string;
    start_date_param: string;
    end_date_param: string;
    rolling_window_days: number;
    tau_groups_info: TauGroupInfo[];
    // ... other metadata
  };
  time_series_data: {
    date: string;
    stock_prices: { adjusted: number };
    bubble_estimates: {
      daily_grouped: {
        put: BubbleEstimate;
        call: BubbleEstimate;
        combined: BubbleEstimate;
      }[];
    };
  }[];
}
```

## 🔒 Environment Variables

For production deployment with Vercel Blob Storage:

```bash
BLOB_READ_WRITE_TOKEN=your_vercel_blob_token
```

See `BLOB_SETUP.md` for detailed setup instructions.

## 📝 License

This project is for research and educational purposes. Please ensure compliance with data usage policies and financial regulations in your jurisdiction.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For questions about the bubble detection methodology or technical implementation, please open an issue in the repository.
