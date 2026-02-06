"""Generate a static index.html with all data embedded."""
import json
import os

os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import app

client = app.test_client()

data = {}
data['rounds'] = client.get('/api/rounds').get_json()
data['chart'] = client.get('/api/cumulative-data').get_json()
data['scores'] = {}
data['standings'] = {}
for r in data['rounds']:
    rid = r['round_id']
    data['scores'][str(rid)] = client.get(f'/api/scores/{rid}').get_json()
    data['standings'][str(rid)] = client.get(f'/api/standings/{rid}').get_json()

json_str = json.dumps(data, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Football Tips</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #0f172a; color: #e2e8f0; min-height: 100vh; }}
        .container {{ max-width: 900px; margin: 0 auto; padding: 2rem 1rem; }}
        h1 {{ text-align: center; font-size: 2rem; margin-bottom: 2rem; color: #f8fafc; }}

        .round-tabs {{ display: flex; gap: 0.5rem; justify-content: center; margin-bottom: 2rem; flex-wrap: wrap; }}
        .round-tabs button {{
            padding: 0.5rem 1.25rem; border: 1px solid #334155; background: #1e293b;
            color: #94a3b8; border-radius: 0.5rem; cursor: pointer; font-size: 0.9rem; transition: all 0.2s;
        }}
        .round-tabs button:hover {{ background: #334155; color: #e2e8f0; }}
        .round-tabs button.active {{ background: #3b82f6; border-color: #3b82f6; color: #fff; }}

        table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; }}
        th {{ background: #1e293b; padding: 0.75rem 1rem; text-align: left; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.05em; color: #94a3b8; }}
        td {{ padding: 0.75rem 1rem; border-bottom: 1px solid #1e293b; }}
        tr:hover td {{ background: #1e293b; }}
        .rank {{ font-weight: 700; color: #f8fafc; width: 3rem; }}
        .rank-1 {{ color: #fbbf24; }}
        .rank-2 {{ color: #d1d5db; }}
        .rank-3 {{ color: #d97706; }}
        .score {{ font-weight: 600; font-variant-numeric: tabular-nums; }}
        .change-up {{ color: #34d399; }}
        .change-down {{ color: #f87171; }}
        .change-same {{ color: #64748b; }}

        .chart-container {{ background: #1e293b; border-radius: 0.75rem; padding: 1.5rem; }}
        h2 {{ font-size: 1.25rem; margin-bottom: 1rem; color: #f8fafc; }}
        canvas {{ width: 100% !important; }}

        .standings-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin-bottom: 2rem; }}
        .standings-panel {{ background: #1e293b; border-radius: 0.75rem; padding: 1rem; overflow-x: auto; }}
        .standings-panel h2 {{ font-size: 1rem; margin-bottom: 0.75rem; }}
        .standings-panel table {{ margin-bottom: 0; font-size: 0.85rem; }}
        .standings-panel th {{ background: #0f172a; padding: 0.5rem 0.6rem; }}
        .standings-panel td {{ padding: 0.5rem 0.6rem; }}
        .match {{ color: #34d399; }}
        .no-match {{ color: #f87171; }}
        @media (max-width: 768px) {{ .standings-grid {{ grid-template-columns: 1fr; }} }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Football Tips</h1>
        <div class="round-tabs" id="roundTabs"></div>
        <table id="scoreTable">
            <thead>
                <tr><th>Rank</th><th>Player</th><th>Cumulative Score</th><th>Change</th></tr>
            </thead>
            <tbody id="scoreBody"></tbody>
        </table>
        <div class="standings-grid">
            <div class="standings-panel">
                <h2 id="predictedTitle">Best Prediction</h2>
                <table>
                    <thead><tr><th>#</th><th>Team</th></tr></thead>
                    <tbody id="predictedBody"></tbody>
                </table>
            </div>
            <div class="standings-panel">
                <h2>Actual Standings</h2>
                <table>
                    <thead><tr><th>#</th><th>Team</th><th>P</th><th>W</th><th>D</th><th>L</th><th>GD</th><th>Pts</th></tr></thead>
                    <tbody id="actualBody"></tbody>
                </table>
            </div>
        </div>
        <div class="chart-container">
            <h2>Rankings Per Round</h2>
            <canvas id="chart" height="300"></canvas>
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
    <script>
        const DATA = {json_str};
        const COLORS = ['#3b82f6','#f59e0b','#10b981','#ef4444','#8b5cf6','#ec4899','#14b8a6','#f97316'];
        let chart = null;

        function init() {{
            const tabs = document.getElementById('roundTabs');
            DATA.rounds.forEach(r => {{
                const btn = document.createElement('button');
                btn.textContent = r.round_name;
                btn.dataset.id = r.round_id;
                btn.onclick = () => selectRound(r.round_id);
                tabs.appendChild(btn);
            }});
            if (DATA.rounds.length) selectRound(DATA.rounds[DATA.rounds.length - 1].round_id);
            loadChart();
        }}

        function selectRound(roundId) {{
            document.querySelectorAll('.round-tabs button').forEach(b =>
                b.classList.toggle('active', parseInt(b.dataset.id) === roundId));
            const scores = DATA.scores[roundId];
            const body = document.getElementById('scoreBody');
            body.innerHTML = scores.map(s => {{
                const cls = s.rank <= 3 ? ` rank-${{s.rank}}` : '';
                let changeCls = 'change-same';
                if (s.rank_change.includes('\\u2191')) changeCls = 'change-up';
                else if (s.rank_change.includes('\\u2193')) changeCls = 'change-down';
                return `<tr>
                    <td class="rank${{cls}}">${{s.rank}}</td>
                    <td>${{s.team_name}}</td>
                    <td class="score">${{s.cumulative_score.toLocaleString()}}</td>
                    <td class="${{changeCls}}">${{s.rank_change}}</td>
                </tr>`;
            }}).join('');
            loadStandings(roundId);
        }}

        function loadStandings(roundId) {{
            const data = DATA.standings[roundId];
            const actualMap = {{}};
            data.actual.forEach(r => {{ actualMap[r.team] = r.position; }});
            document.getElementById('predictedTitle').textContent =
                `Best Prediction (${{data.best_user}})`;
            document.getElementById('predictedBody').innerHTML = data.predicted.map(r => {{
                const actualPos = actualMap[r.team];
                const cls = actualPos === r.position ? 'match' : 'no-match';
                return `<tr>
                    <td class="rank">${{r.position}}</td>
                    <td class="${{cls}}">${{r.team}}</td>
                </tr>`;
            }}).join('');
            document.getElementById('actualBody').innerHTML = data.actual.map(r => {{
                return `<tr>
                    <td class="rank">${{r.position}}</td>
                    <td>${{r.team}}</td>
                    <td>${{r.played}}</td>
                    <td>${{r.w}}</td>
                    <td>${{r.d}}</td>
                    <td>${{r.l}}</td>
                    <td>${{r.gd}}</td>
                    <td>${{r.pts}}</td>
                </tr>`;
            }}).join('');
        }}

        function loadChart() {{
            const data = DATA.chart;
            const ctx = document.getElementById('chart').getContext('2d');
            const teams = Object.keys(data.teams);
            chart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: data.rounds,
                    datasets: teams.map((name, i) => ({{
                        label: name,
                        data: data.teams[name],
                        borderColor: COLORS[i % COLORS.length],
                        backgroundColor: COLORS[i % COLORS.length] + '22',
                        tension: 0.3,
                        pointRadius: 4,
                        borderWidth: 2
                    }}))
                }},
                options: {{
                    responsive: true,
                    plugins: {{
                        legend: {{
                            labels: {{ color: '#94a3b8' }},
                            onClick: (e, legendItem, legend) => {{
                                const index = legendItem.datasetIndex;
                                const ci = legend.chart;
                                const isHighlighted = ci.data.datasets[index].borderWidth === 4;
                                ci.data.datasets.forEach((ds, i) => {{
                                    if (isHighlighted) {{
                                        ds.borderWidth = 2;
                                        ds.borderColor = COLORS[i % COLORS.length];
                                        ds.pointRadius = 4;
                                    }} else {{
                                        if (i === index) {{
                                            ds.borderWidth = 4;
                                            ds.pointRadius = 6;
                                        }} else {{
                                            ds.borderWidth = 1;
                                            ds.borderColor = COLORS[i % COLORS.length] + '33';
                                            ds.pointRadius = 2;
                                        }}
                                    }}
                                }});
                                ci.update();
                            }}
                        }}
                    }},
                    scales: {{
                        x: {{ ticks: {{ color: '#64748b' }}, grid: {{ color: '#1e293b' }} }},
                        y: {{ reverse: true, ticks: {{ color: '#64748b', stepSize: 1 }}, grid: {{ color: '#1e293b' }} }}
                    }}
                }}
            }});
        }}

        init();
    </script>
</body>
</html>'''

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Generated index.html ({len(html)} bytes)')
