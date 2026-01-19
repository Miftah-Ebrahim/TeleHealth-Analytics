# TeleHealth-Analytics

**TeleHealth-Analytics** is a data engineering project designed to scrape, clean, and store Telegram channel data for analysis. The system scrapes messages and images from specified channels, loads them into a PostgreSQL database, and performs data transformation using dbt.

## 📁 Project Structure

```
├── .github/                # GitHub Actions/Workflows
├── api/                    # API endpoints (if applicable)
├── dbt_project/            # dbt transformations
│   ├── models/             # Staging and Marts models
│   ├── tests/              # Custom data quality tests
│   └── profiles.yml        # dbt connection profile
├── src/
│   ├── collectors/         # Scraping scripts
│   │   └── telegram_scraper.py
│   └── loaders/            # Database loading scripts
│       └── postgres_loader.py
├── data/                   # Data storage (ignored by git)
│   └── raw/
├── docker-compose.yml      # Docker services
├── README.md               # Project documentation
└── requirements.txt        # Python dependencies
```

## 🚀 Getting Started

### Prerequisites
- Docker & Docker Compose
- Python 3.9+
- Telegram API Credentials (`TG_API_ID`, `TG_API_HASH`)

### 1. Setup Environment
Create a `.env` file in the root directory:
```bash
TG_API_ID=your_api_id
TG_API_HASH=your_api_hash
```

### 2. Run Database
Start the Postgres container:
```bash
docker-compose up -d
```

### 3. Collect Data (Scraper)
Run the scraper to fetch messages and images:
```bash
python src/collectors/telegram_scraper.py
```
*Data will be saved in `data/raw/telegram_messages/YYYY-MM-DD/` and `data/raw/images/`.*

### 4. Load Data (Loader)
Load the JSON data into PostgreSQL:
```bash
python src/loaders/postgres_loader.py
```

### 5. Transform Data (dbt)
Navigate to the dbt project and run transformations:
```bash
cd dbt_project
dbt build
```

## 📊 Data Pipeline
1.  **Ingestion**: `telegram_scraper.py` uses Telethon to scrape messages.
2.  **Loading**: `postgres_loader.py` recursively finds JSON files and loads them to `raw.telegram_messages`.
3.  **Transformation**: dbt cleans and models data into:
    -   `stg_telegram`: Staging layer with calculated fields.
    -   `dim_channels`: Channel statistics.
    -   `dim_dates`: Date dimension.
    -   `fct_messages`: Fact table for analysis.

## 🧪 Testing
Run dbt tests to ensure data quality:
```bash
dbt test
```
*Includes checks for non-negative views and valid message dates.*
