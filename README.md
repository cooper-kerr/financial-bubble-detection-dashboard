# Financial Bubble Detection Dashboard

A sophisticated web application for visualizing and analyzing financial bubble estimates using options data. This dashboard provides interactive time-series visualizations of bubble probability estimates across different time horizons (tau groups) for major stocks and indices.

## 🎯 Overview

This research dashboard implements a financial bubble detection methodology that analyzes options market data to estimate the probability of asset price bubbles. The system processes put and call options data to generate bubble estimates with confidence intervals across multiple time horizons.

### Key Features

- **Interactive Time-Series Visualization**: Dynamic Plotly charts with enhanced tooltips and dark mode support
- **Multi-Asset Analysis**: Support for 26 major stocks and indices (SPX, AAPL, TSLA, etc.)
- **Tau Group Analysis**: Three different time horizon groups for bubble detection (τ ≈ 0.25, 0.5, 1.0)
- **Options Data Integration**: Separate analysis for put options, call options, and combined estimates
- **Price Comparison Charts**: Split-adjusted vs. raw price visualization
- **Confidence Intervals**: Statistical bounds (upper/lower) for all bubble estimates
- **Date Range Filtering**: Customizable time period selection with date pickers
- **Responsive Design**: Modern UI with dark/light theme support and mobile optimization
- **Cloud Data Storage**: Vercel Blob Storage integration

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

## Data Sources
### WRDS (1996-2023)
- **Stock Price Data**: Split-adjusted historical prices 
- **Options Data**: Put and call options with various expiration dates
- **Time Series**: Daily bubble estimates with rolling window analysis
### Yahoo Finance API (2026 - Present)
- **Stock Price Data**: Uses Yahoo Finance API
- **Options Data**: Uses Yahoo Finance API
- **Dashboard**: Seperate section on dashboard to show most recent bubble estimates using data from Yahoo Finance



## 🚀 Getting Started

### Prerequisites

- [Bun](https://bun.sh/) runtime
- Modern web browser with JavaScript enabled

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

3. **Environment Setup (Optional for Production)**

   For Vercel Blob Storage integration, create a `.env.local` file:

   ```bash
   BLOB_READ_WRITE_TOKEN=your_vercel_blob_token
   ```

   See `BLOB_SETUP.md` for detailed setup instructions.

4. **Start the development server**

   ```bash
   bun run start
   # or
   bun run dev
   ```

   The application will be available at `http://localhost:3000`

## 🏗️ Building for Production

```bash
bun run build
```

This creates an optimized production build in the `dist/` directory with TypeScript compilation.

## 📁 Project Structure

```
financial-bubble-detection-dashboard/
├── src/
│   ├── components/              # React components
│   │   ├── Dashboard.tsx        # Main dashboard component
│   │   ├── DashboardControls.tsx # Control panel with stock/date selectors
│   │   ├── PlotlyBubbleChart.tsx # Interactive Plotly charts
│   │   ├── PriceDifferenceChart.tsx # Price comparison charts
│   │   ├── LoadingSpinner.tsx   # Loading state component
│   │   ├── date-picker.tsx      # Custom date picker component
│   │   ├── theme-provider.tsx   # Theme context provider
│   │   ├── theme-switcher.tsx   # Dark/light mode toggle
│   │   └── ui/                  # Reusable UI components (shadcn/ui)
│   │       ├── button.tsx       # Button component
│   │       ├── card.tsx         # Card component
│   │       ├── calendar.tsx     # Calendar component
│   │       ├── select.tsx       # Select dropdown component
│   │       └── popover.tsx      # Popover component
│   ├── hooks/                   # Custom React hooks
│   │   └── useDashboardData.ts  # Main data management hook
│   ├── lib/                     # Utility libraries
│   │   └── utils.ts             # Common utility functions
│   ├── routes/                  # TanStack Router routes
│   │   ├── __root.tsx           # Root route layout
│   │   └── index.tsx            # Home page route
│   ├── types/                   # TypeScript type definitions
│   │   └── bubbleData.ts        # Data structure interfaces
│   ├── utils/                   # Utility functions
│   │   └── dataLoader.ts        # Data fetching and processing
│   ├── styles/                  # CSS and styling
│   │   └── styles.css           # Global styles and Tailwind imports
│   ├── main.tsx                 # Application entry point
│   └── routeTree.gen.ts         # Generated route tree (auto-generated)
├── scripts/                     # Utility scripts
│   ├── upload-to-blob.ts        # Upload data to Vercel Blob Storage
│   ├── get-blob-urls.ts         # Retrieve blob URLs
│   ├── test-blob-fetch.ts       # Test blob connectivity
│   └── update-blob-urls.ts      # Update URL mappings
├── docs/                        # Documentation
│   └── plotly-tooltip-customization-guide.md
├── public/                      # Static assets
│   └── *.png, *.ico, etc.       # Images and icons
├── dist/                        # Production build output
├── package.json                 # Dependencies and scripts
├── vite.config.ts               # Vite configuration
├── tsconfig.json                # TypeScript configuration
├── biome.json                   # Biome linter/formatter config
├── components.json              # shadcn/ui configuration
├── vercel.json                  # Vercel deployment config
├── BLOB_SETUP.md                # Blob storage setup guide
└── README.md                    # This file
```

## 📈 Available Stocks

The dashboard supports analysis for the following assets:

- **Indices**: SPX (S&P 500)
- **Technology**: AAPL, MSFT, GOOG, AMZN, NVDA, INTC, CSCO, AMD
- **Financial**: JPM, BAC, C, WFC, MS, AIG
- **Other Sectors**: TSLA, F, GM, DIS, BA, GE, XOM, T, BABA, TWTR

## 🎨 Features

### Interactive Charts

- **Advanced Plotly Integration**: High-performance interactive charts with zoom, pan, and selection
- **Enhanced Tooltips**: Custom-styled tooltips with dark mode support and rich formatting
- **Multi-Series Visualization**: Simultaneous display of all tau groups and stock prices
- **Time Range Selection**: Date picker controls for custom time period analysis
- **Chart Types**:
  - Put Options Bubble Estimates (μ̂_p(τ))
  - Call Options Bubble Estimates (μ̂_c(τ))
  - Combined Options Bubble Estimates (μ̂_cp(τ))
  - Price Comparison Charts (Split-adjusted vs. Raw prices)

### Data Management

- **Cloud Storage**: Vercel Blob Storage for production data hosting
- **Efficient Loading**: Optimized data fetching with error handling and loading states
- **Data Processing**: Real-time transformation of bubble estimates and price data
- **Caching Strategy**: Smart data caching to minimize API calls

### User Interface

- **Modern Design System**: Built with shadcn/ui components and Tailwind CSS
- **Responsive Layout**: Optimized for desktop, tablet, and mobile devices
- **Theme Support**: Seamless light/dark mode toggle with system preference detection
- **Loading States**: Smooth loading indicators and skeleton screens
- **Accessibility**: ARIA labels, keyboard navigation, and screen reader support
- **Error Handling**: Graceful error states with retry functionality

## 🔧 Development

### Available Scripts

```bash
# Development
bun run dev          # Start development server (alias for start)
bun run start        # Start development server on port 3000
bun run build        # Build for production with TypeScript compilation
bun run serve        # Preview production build

# Testing
bun run test         # Run Vitest test suite

# Code Quality
bun run lint         # Check code quality with Biome
bun run format       # Format code with Biome
bun run check        # Run both lint and format checks

# Data Management
bun run upload-data  # Upload JSON files to Vercel Blob Storage
bun run get-blob-urls # Retrieve current blob URLs
bun run test-blob    # Test blob storage connectivity
```

### Development Workflow

1. **Local Development**: Use `bun run dev` for hot-reload development
2. **Code Quality**: Run `bun run check` before committing
3. **Testing**: Execute `bun run test` to run the test suite
4. **Data Updates**: Use blob scripts to manage production data
5. **Production Build**: Test with `bun run build && bun run serve`

## 🛠️ Technology Stack

### Core Technologies

- **Frontend Framework**: React 19 with TypeScript
- **Build Tool**: Vite 6.1.0 with hot module replacement
- **Package Manager**: Bun
- **Routing**: TanStack Router with file-based routing

### UI & Styling

- **Charts**: Plotly.js with react-plotly.js for interactive visualizations
- **Styling**: Tailwind CSS 4.1.11 with CSS variables
- **UI Components**: shadcn/ui built on Radix UI primitives
- **Icons**: Lucide React icon library
- **Math Rendering**: KaTeX for mathematical expressions

### Development Tools

- **Testing**: Vitest with jsdom environment
- **Code Quality**: Biome for linting and formatting
- **Type Checking**: TypeScript 5.7.2 with strict mode
- **Performance**: Web Vitals monitoring

### Data & Storage

- **Cloud Storage**: Vercel Blob Storage for production data
- **Data Processing**: Custom utilities for bubble estimate calculations

### Deployment

- **Platform**: Vercel with optimized build configuration
- **Environment**: Node.js 18+ runtime support

## 📊 Data Format

The application expects JSON data files with the following structure:

### Bubble Data Structure

```typescript
interface BubbleData {
  metadata: {
    stockcode: string; // Stock symbol (e.g., "SPX", "AAPL")
    start_date_param: string; // Analysis start date
    end_date_param: string; // Analysis end date
    rolling_window_days: number; // Rolling window size
    num_steps: number; // Number of optimization steps
    optimization_threshold: number; // Convergence threshold
    h_number_sd: number; // Standard deviation parameter
    tau_groups_info: TauGroupInfo[]; // Tau group definitions
    option_types_info: string[]; // Option types analyzed
    time_series_start_date: string; // Time series start
    time_series_end_date: string; // Time series end
  };
  time_series_data: TimeSeriesDataPoint[];
}

interface TimeSeriesDataPoint {
  date: string; // ISO date string
  stock_prices: {
    adjusted: number; // Split-adjusted price
    regular?: number; // Raw price (optional)
  };
  bubble_estimates: {
    daily_grouped: DailyGroupedData[]; // One per tau group
  };
}

interface DailyGroupedData {
  put: BubbleEstimate; // Put option estimates
  call: BubbleEstimate; // Call option estimates
  combined: BubbleEstimate; // Combined estimates
}

interface BubbleEstimate {
  mu: number; // Point estimate
  lb: number; // Lower bound
  ub: number; // Upper bound
}

interface TauGroupInfo {
  name: string; // Group name (e.g., "Tau Group 1")
  range: string; // Range description
  mean: number; // Mean tau value
}
```

### Regular Price Data Structure

```typescript
interface RegularPriceData {
  date: string; // ISO date string
  price: number; // Raw stock price
}
```

## 🔒 Environment Variables

For production deployment with Vercel Blob Storage:

```bash
BLOB_READ_WRITE_TOKEN=your_vercel_blob_token
```

See `BLOB_SETUP.md` for detailed setup instructions.

## 🧪 Testing

The project uses Vitest for testing with jsdom environment:

```bash
# Run all tests
bun run test

# Run tests in watch mode (development)
bun run test --watch

# Run tests with coverage
bun run test --coverage
```

## 📝 License

This project is for research and educational purposes. Please ensure compliance with data usage policies and financial regulations in your jurisdiction.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Run tests and linting (`bun run check && bun run test`)
4. Commit your changes (`git commit -m 'Add amazing feature'`)
5. Push to the branch (`git push origin feature/amazing-feature`)
6. Open a Pull Request

### Development Guidelines

- Follow TypeScript best practices
- Use Biome for code formatting and linting
- Write tests for new features
- Update documentation as needed
- Ensure responsive design compatibility

## 📞 Support

For questions about the bubble detection methodology or technical implementation, please open an issue in the repository.

## 📚 Additional Resources

- **[BLOB_SETUP.md](./BLOB_SETUP.md)**: Detailed guide for setting up Vercel Blob Storage
- **[Plotly.js Documentation](https://plotly.com/javascript/)**: Official Plotly documentation
- **[TanStack Router](https://tanstack.com/router)**: Router documentation
- **[shadcn/ui](https://ui.shadcn.com/)**: UI component library documentation
