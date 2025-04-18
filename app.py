from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz
import os
import logging

app = Flask(__name__)

# Set up logging for debugging on Vercel
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the base URL
BASE_URL = "https://www.yallakora.com/match-center/%D9%85%D8%B1%D9%83%D8%B2-%D8%A7%D9%84%D9%85%D8%A8%D8%A7%D8%B1%D9%8A%D8%A7%D8%AA"

def get_egypt_time():
    """Gets the current time in Egypt."""
    egypt_timezone = pytz.timezone('Africa/Cairo')
    now_utc = datetime.utcnow()
    now_egypt = now_utc.replace(tzinfo=pytz.utc).astimezone(egypt_timezone)
    return now_egypt

def format_date_for_url(date_obj):
    """Formats a datetime object as YYYY-MM-DD for the form input."""
    return date_obj.strftime("%Y-%m-%d")

def format_date_for_yallakora(date_str):
    """Converts YYYY-MM-DD to MM/DD/YYYY for Yalla Kora URL."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%m/%d/%Y")
    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        return format_date_for_url(get_egypt_time())

def create_url(date_str=None):
    """Creates the full Yalla Kora URL with the specified date."""
    if date_str:
        formatted_date = format_date_for_yallakora(date_str)
        return f"{BASE_URL}?date={formatted_date}#days"
    else:
        current_egypt_time = get_egypt_time()
        default_date_str = format_date_for_yallakora(format_date_for_url(current_egypt_time))
        return f"{BASE_URL}?date={default_date_str}#days"

def scrape_matches(url):
    """Scrapes match data from the given Yalla Kora URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        match_cards = soup.find_all("div", class_="matchCard")
        all_matches = []

        for card in match_cards:
            championship_name_tag = card.find("h2")
            championship = championship_name_tag.text.strip() if championship_name_tag else "N/A"

            matches = card.find_all("div", class_="item")
            for match in matches:
                team_a_tag = match.find("div", class_="teamA")
                team_b_tag = match.find("div", class_="teamB")
                team_a = team_a_tag.p.text.strip() if team_a_tag and team_a_tag.p else "N/A"
                team_b = team_b_tag.p.text.strip() if team_b_tag and team_b_tag.p else "N/A"

                result_tag = match.find("div", class_="MResult")
                if result_tag:
                    scores = result_tag.find_all("span", class_="score")
                    result = f"{scores[0].text.strip()} - {scores[1].text.strip()}" if len(scores) >= 2 else "N/A"
                else:
                    result = "N/A"

                all_matches.append([championship, team_a, team_b, result])

        logger.info(f"Scraped {len(all_matches)} matches from {url}")
        return all_matches

    except requests.RequestException as e:
        logger.error(f"Error fetching data from {url}: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error while scraping {url}: {e}")
        return []

@app.route("/", methods=["GET", "POST"])
def index():
    matches_data = []
    selected_date = request.form.get("date") if request.method == "POST" else format_date_for_url(get_egypt_time())
    url = create_url(selected_date)
    matches_data = scrape_matches(url)
    return render_template(
        "index.html",
        matches=matches_data,
        format_date_for_url=format_date_for_url,
        get_egypt_time=get_egypt_time
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)