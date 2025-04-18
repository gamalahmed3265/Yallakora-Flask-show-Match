from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import os

app = Flask(__name__)

def get_egypt_time():
    """Get current time in Egypt timezone."""
    egypt_tz = pytz.timezone('Africa/Cairo')
    return datetime.now(egypt_tz)

def format_date_for_url(dt):
    """Format date as YYYY-MM-DD for form input."""
    return dt.strftime('%Y-%m-%d')

def scrape_matches(date):
    """
    Scrape match data from Yalla Kora for the given date.
    Returns a list of tuples: (tournament, team_a, team_b, score).
    """
    try:
        # Example URL (replace with actual Yalla Kora URL for the date)
        # Yalla Kora's URL structure may be like: https://www.yallakora.com/Match-Center/?date=YYYY-MM-DD
        url = f"https://www.yallakora.com/Match-Center/?date={date}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        matches = []

        # Example scraping logic (adjust based on Yalla Kora's HTML structure)
        # Inspect the website's HTML to find the correct selectors
        match_cards = soup.select('.matchCard')  # Hypothetical selector; inspect actual HTML
        for card in match_cards:
            tournament = card.select_one('.championShip .title') or 'Unknown'
            team_a = card.select_one('.teamA .teamName') or 'Team A'
            team_b = card.select_one('.teamB .teamName') or 'Team B'
            score = card.select_one('.score') or '0 - 0'
            matches.append((
                tournament.get_text(strip=True) if hasattr(tournament, 'get_text') else 'Unknown',
                team_a.get_text(strip=True) if hasattr(team_a, 'get_text') else 'Team A',
                team_b.get_text(strip=True) if hasattr(team_b, 'get_text') else 'Team B',
                score.get_text(strip=True) if hasattr(score, 'get_text') else '0 - 0'
            ))

        return matches

    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

@app.route('/', methods=['GET', 'POST'])
def home():
    selected_date = request.form.get('date') if request.method == 'POST' else format_date_for_url(get_egypt_time())
    matches = scrape_matches(selected_date) if selected_date else []
    return render_template('index.html', matches=matches, format_date_for_url=format_date_for_url, get_egypt_time=get_egypt_time)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)