from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

app = Flask(__name__)

# Define the base URL
BASE_URL = "https://www.yallakora.com/match-center/%D9%85%D8%B1%D9%83%D8%B2-%D8%A7%D9%84%D9%85%D8%A8%D8%A7%D8%B1%D9%8A%D8%A7%D8%AA"

def get_egypt_time():
    """Gets the current time in Egypt."""
    egypt_timezone = pytz.timezone('Africa/Cairo')
    now_utc = datetime.utcnow()
    now_egypt = now_utc.replace(tzinfo=pytz.utc).astimezone(egypt_timezone)
    return now_egypt

def format_date_for_url(date_obj):
    """Formats a datetime object as MM/DD/YYYY for the URL."""
    return date_obj.strftime("%m/%d/%Y")

def create_url(date_str=None):
    """Creates the full Yalla Kora URL with the specified date."""
    if date_str:
        return f"{BASE_URL}?date={date_str}#days"
    else:
        current_egypt_time = get_egypt_time()
        default_date_str = format_date_for_url(current_egypt_time)
        return f"{BASE_URL}?date={default_date_str}#days"

def scrape_matches(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")

    match_cards = soup.find_all("div", class_="matchCard")
    all_matches = []

    for card in match_cards:
        championship_name_tag = card.find("h2")
        if not championship_name_tag:
            continue
        championship = championship_name_tag.text.strip()

        matches = card.find_all("div", class_="item")

        for match in matches:
            team_a = match.find("div", class_="teamA").p.text.strip()
            team_b = match.find("div", class_="teamB").p.text.strip()

            result_tag = match.find("div", class_="MResult")
            if result_tag:
                scores = result_tag.find_all("span", class_="score")
                result = f"{scores[0].text.strip()} - {scores[1].text.strip()}" if len(scores) >= 2 else "N/A"
            else:
                result = "N/A"

            all_matches.append([championship, team_a, team_b, result])
    return all_matches

@app.route("/", methods=["GET", "POST"])
def index():
    matches_data = []
    if request.method == "POST":
        date_input = request.form.get("date")
        url = create_url(date_input)
        matches_data = scrape_matches(url)
    else: # GET request
        url = create_url()
        matches_data = scrape_matches(url)
    return render_template("index.html", matches=matches_data)

if __name__ == "__main__":
    app.run(debug=True)