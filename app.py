from flask import Flask, render_template, jsonify
import duckdb

app = Flask(__name__)

# Database connection
DB_PATH = 'football.duckdb'

def get_db():
    """Get database connection"""
    return duckdb.connect(DB_PATH, read_only=True)

@app.route('/')
def index():
    """Render main page"""
    return render_template('index.html')

@app.route('/api/rounds')
def get_rounds():
    """Get all available rounds"""
    conn = get_db()
    rounds = conn.execute("""
        SELECT DISTINCT round
        FROM analytical.calculated_results
        ORDER BY round
    """).fetchall()
    conn.close()

    return jsonify([{
        'round_id': r[0],
        'round_number': r[0],
        'round_name': f'Round {r[0]}'
    } for r in rounds])

@app.route('/api/scores/<int:round_id>')
def get_scores_by_round(round_id):
    """Get scores for a specific round (lower score = better)"""
    conn = get_db()

    scores = conn.execute("""
        WITH current AS (
            SELECT
                user_name,
                total_diff_pts AS score,
                ROW_NUMBER() OVER (ORDER BY total_diff_pts ASC) AS rank
            FROM analytical.calculated_results
            WHERE round = ?
        ),
        prev AS (
            SELECT
                user_name,
                ROW_NUMBER() OVER (ORDER BY total_diff_pts ASC) AS rank
            FROM analytical.calculated_results
            WHERE round = ? - 1
        )
        SELECT
            c.user_name,
            c.score,
            c.rank,
            CASE
                WHEN ? = 1 THEN '—'
                WHEN p.rank IS NULL THEN '—'
                WHEN p.rank - c.rank > 0 THEN '↑' || CAST(p.rank - c.rank AS VARCHAR)
                WHEN p.rank - c.rank < 0 THEN '↓' || CAST(c.rank - p.rank AS VARCHAR)
                ELSE '—'
            END AS rank_change
        FROM current c
        LEFT JOIN prev p ON c.user_name = p.user_name
        ORDER BY c.rank
    """, [round_id, round_id, round_id]).fetchall()

    conn.close()

    return jsonify([{
        'team_name': s[0],
        'cumulative_score': s[1],
        'rank': s[2],
        'rank_change': s[3]
    } for s in scores])

@app.route('/api/standings/<int:round_id>')
def get_standings(round_id):
    """Get actual league standings and best prediction for a round"""
    conn = get_db()

    # Actual standings for this round
    actual = conn.execute("""
        SELECT position, team, played, w, d, l, gf, ga, gd, pts
        FROM analytical.round_standings
        WHERE round = ?
        ORDER BY position
    """, [round_id]).fetchall()

    # Find the best predictor for this round
    best_user = conn.execute("""
        SELECT user_name
        FROM analytical.calculated_results
        WHERE round = ?
        ORDER BY total_diff_pts ASC
        LIMIT 1
    """, [round_id]).fetchone()

    # Get that user's predicted standings
    predicted = []
    if best_user:
        predicted = conn.execute("""
            SELECT position, team_name
            FROM analytical.union_all_tips
            WHERE user_name = ?
            ORDER BY position
        """, [best_user[0]]).fetchall()

    conn.close()

    return jsonify({
        'actual': [{
            'position': r[0], 'team': r[1], 'played': r[2],
            'w': r[3], 'd': r[4], 'l': r[5],
            'gf': r[6], 'ga': r[7], 'gd': r[8], 'pts': r[9]
        } for r in actual],
        'predicted': [{
            'position': r[0], 'team': r[1]
        } for r in predicted],
        'best_user': best_user[0] if best_user else None
    })

@app.route('/api/cumulative-data')
def get_cumulative_data():
    """Get per-round ranking data for all rounds and users"""
    conn = get_db()

    data = conn.execute("""
        SELECT
            user_name,
            round,
            ROW_NUMBER() OVER (PARTITION BY round ORDER BY total_diff_pts ASC) AS rank
        FROM analytical.calculated_results
        ORDER BY user_name, round
    """).fetchall()

    conn.close()

    # Build chart data grouped by user
    chart_data = {}
    rounds_set = set()
    for user_name, round_num, rank in data:
        rounds_set.add(round_num)
        if user_name not in chart_data:
            chart_data[user_name] = {}
        chart_data[user_name][round_num] = int(rank)

    sorted_rounds = sorted(rounds_set)
    teams = {
        user: [ranks.get(r, 0) for r in sorted_rounds]
        for user, ranks in chart_data.items()
    }

    return jsonify({
        'rounds': [f"Round {r}" for r in sorted_rounds],
        'teams': teams
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
