# Tournament Results Dashboard - DuckDB + Python Flask

A modern, dark-mode sports tournament results dashboard powered by DuckDB and Flask.

## Features

- 🦆 **DuckDB Backend**: Fast, embedded SQL database for tournament data
- 🐍 **Python Flask**: RESTful API endpoints for data retrieval
- 📊 **Interactive Charts**: Real-time cumulative score visualization
- 📱 **Responsive Design**: Desktop and mobile layouts
- 🌙 **Dark Mode**: Modern, eye-friendly interface
- ⚡ **Real-time Updates**: Dynamic data loading from database

## Architecture

```
┌─────────────────┐
│   Flask App     │
│   (app.py)      │
└────────┬────────┘
         │
         ├─── API Endpoints (/api/*)
         │    ├── /api/rounds
         │    ├── /api/scores/<round_id>
         │    ├── /api/cumulative-data
         │    └── /api/add-score
         │
         ├─── DuckDB Database
         │    └── tournament_results.db
         │         ├── teams table
         │         ├── rounds table
         │         └── scores table
         │
         └─── Frontend (templates/index.html)
              ├── Chart.js for graphs
              └── Fetch API for data
```

## Database Schema

### Teams Table
- `team_id` (INTEGER, PRIMARY KEY)
- `team_name` (VARCHAR)
- `created_at` (TIMESTAMP)

### Rounds Table
- `round_id` (INTEGER, PRIMARY KEY)
- `round_number` (INTEGER)
- `round_name` (VARCHAR)
- `round_date` (DATE)

### Scores Table
- `score_id` (INTEGER, PRIMARY KEY)
- `team_id` (INTEGER, FOREIGN KEY)
- `round_id` (INTEGER, FOREIGN KEY)
- `score` (INTEGER)
- `cumulative_score` (INTEGER)
- `rank` (INTEGER)
- `rank_change` (VARCHAR)

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install flask duckdb
```

2. Run the application:
```bash
python app.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## API Endpoints

### GET /api/rounds
Returns all available tournament rounds.

**Response:**
```json
[
  {
    "round_id": 1,
    "round_number": 1,
    "round_name": "Round 1",
    "round_date": "2024-01-15"
  }
]
```

### GET /api/scores/<round_id>
Returns scores for a specific round.

**Response:**
```json
[
  {
    "team_name": "Thunder Ravens",
    "cumulative_score": 728,
    "rank": 1,
    "rank_change": "—"
  }
]
```

### GET /api/cumulative-data
Returns all cumulative score data for chart visualization.

**Response:**
```json
{
  "rounds": ["Round 1", "Round 2", "Round 3"],
  "teams": {
    "Lightning Strikers": [245, 476, 715],
    "Thunder Ravens": [238, 482, 728]
  }
}
```

### POST /api/add-score
Add a new score entry to the database.

**Request Body:**
```json
{
  "team_id": 1,
  "round_id": 6,
  "score": 250,
  "cumulative_score": 1471,
  "rank": 2,
  "rank_change": "—"
}
```

**Response:**
```json
{
  "success": true,
  "score_id": 26
}
```

## Database Initialization

The database is automatically initialized with sample data on first run:
- 5 teams (Lightning Strikers, Thunder Ravens, Storm Chasers, Phoenix Rising, Dragon Force)
- 5 rounds of competition
- Complete score history with rankings and changes

## Customization

### Adding New Teams
```python
conn.execute("INSERT INTO teams (team_id, team_name) VALUES (?, ?)", [6, 'New Team Name'])
```

### Adding New Rounds
```python
conn.execute("INSERT INTO rounds (round_id, round_number, round_name, round_date) VALUES (?, ?, ?, ?)", 
             [6, 6, 'Round 6', '2024-02-19'])
```

### Updating Scores
Use the `/api/add-score` endpoint or directly insert into the database:
```python
conn.execute("""
    INSERT INTO scores (score_id, team_id, round_id, score, cumulative_score, rank, rank_change)
    VALUES (?, ?, ?, ?, ?, ?, ?)
""", [26, 1, 6, 250, 1471, 2, '↑1'])
```

## Technologies Used

- **Backend**: Python 3.x, Flask
- **Database**: DuckDB (embedded SQL database)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **Charts**: Chart.js
- **Design**: Custom dark mode theme with gradient effects

## File Structure

```
tournament-results/
├── app.py                      # Flask application and API
├── requirements.txt            # Python dependencies
├── tournament_results.db       # DuckDB database (auto-created)
├── templates/
│   └── index.html             # Main frontend template
└── README.md                  # This file
```

## Development

The application runs in debug mode by default, which provides:
- Auto-reload on code changes
- Detailed error messages
- Development server on all interfaces (0.0.0.0:5000)

For production deployment, set `debug=False` in `app.py` and use a production WSGI server like Gunicorn.

## Notes

- The database file (`tournament_results.db`) is created automatically on first run
- Sample data is only inserted if the database is empty
- All API endpoints return JSON responses
- The frontend uses the Fetch API for asynchronous data loading
- Chart.js is loaded from CDN for visualization

## Future Enhancements

- Add authentication for score submissions
- Implement real-time updates with WebSockets
- Add team statistics and analytics
- Export data to CSV/Excel
- Add admin panel for data management
- Implement search and filtering
- Add historical comparisons
