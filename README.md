# DCF Valuation Engine

A web-based Discounted Cash Flow (DCF) valuation tool that calculates 12-month target prices for publicly traded companies.

## Features

- **Interactive DCF Calculator**: Input ticker symbol and growth assumptions
- **Real-Time Financial Data**: Fetches live data from Financial Modeling Prep API
- **Transparent Calculations**: View detailed calculation logs for every valuation
- **Professional Interface**: Clean, financial-themed design optimized for analysis
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Technology Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **Data Source**: Financial Modeling Prep API
- **Hosting**: Render (free tier)

## Local Development

### Prerequisites

- Python 3.9 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd dcf_webapp
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Deployment to Render

### Step 1: Prepare Your Repository

1. Create a GitHub account if you don't have one
2. Create a new repository on GitHub
3. Initialize git in your project folder and push:
```bash
cd dcf_webapp
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Deploy on Render

1. Go to [render.com](https://render.com) and sign up (free)
2. Click "New +" and select "Web Service"
3. Connect your GitHub account and select your repository
4. Configure the service:
   - **Name**: dcf-valuation-engine (or your preferred name)
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Free

5. Add Environment Variable (optional, recommended for production):
   - Key: `FMP_API_KEY`
   - Value: Your Financial Modeling Prep API key

6. Click "Create Web Service"

Your app will be live at: `https://your-app-name.onrender.com`

**Note**: The free tier may have cold starts (takes ~30 seconds to wake up after inactivity).

## Usage

1. Enter a stock ticker symbol (e.g., AAPL, MSFT, GOOGL)
2. Input revenue growth rates for the next 5 years (as decimals, e.g., 0.05 for 5%)
3. Enter the terminal growth rate (typically 2-3%)
4. Click "Calculate Valuation"
5. Review the 12-month target price and detailed metrics
6. Click "View Detailed Calculations" to see the full DCF breakdown

## API Rate Limits

The application uses the Financial Modeling Prep API with the following considerations:
- Free tier has rate limits (typically 250 requests/day)
- Market return and risk-free rate are set to defaults due to API limitations
- Historical data is limited to the last 5 years

## Future Enhancements

Potential features to add:
- User authentication and saved valuations
- Multiple valuation models (DDM, Comparable Company Analysis, etc.)
- Scenario analysis and sensitivity tables
- Excel export functionality
- Portfolio tracking
- Comparison with analyst estimates

## Data Sources & Disclaimer

- Financial data provided by Financial Modeling Prep API
- Market data and calculations are for educational purposes only
- This tool does not constitute financial advice
- Always conduct thorough research before making investment decisions

## License

MIT License - Feel free to modify and use for your own projects

## Support

For issues or questions, please open an issue on GitHub or contact the maintainer.
