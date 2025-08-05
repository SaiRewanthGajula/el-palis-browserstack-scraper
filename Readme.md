# El País Opinion Section Scraper (BrowserStack Assignment)

Hi! 👋  
This project is my submission for the BrowserStack Customer Engineering assignment. It demonstrates automation, web scraping, text processing, translation, and robust cross-browser testing using Selenium with BrowserStack.

---

## What This Script Does

- **Visits** the [El País](https://elpais.com/) "Opinion" section.
- **Scrapes** the first five articles: grabs the title, content (in Spanish), and downloads the cover image if one is shown.
- **Translates** each title to English using the Google Translate API (free tier).
- **Prints** both the Spanish originals and English headers.
- **Counts** any word that appears more than twice across the translated headers and prints that as well.
- **Runs automatically** both locally (Chrome headless), and across 5 parallel BrowserStack browsers/devices (Windows Chrome, Mac Firefox, iPhone Safari, Samsung Chrome, Windows Edge).

---

## How to Run

### 1. Install Python Requirements

pip install selenium deep-translator python-dotenv


- Make sure you have a compatible `chromedriver` installed for local runs (and available in your system PATH).

### .env file setup

Create a file named `.env` in the project root with these lines:

BROWSERSTACK_USERNAME=your_browserstack_username
BROWSERSTACK_ACCESS_KEY=your_browserstack_access_key

# (optional) for DeepL (replace with your actual key)
# DEEPL_AUTH_KEY=your_deepl_auth_key


### 3. Run the Script

Run this in your terminal (PowerShell/CMD):

python scrape_el_pais.py


- It will first do a local (headless Chrome) run to verify everything works.
- Then it will start 5 parallel BrowserStack sessions—across popular browser/OS/device combinations, real-world style.
- Results, including translated headers, repeated word analysis, and the image downloads, are printed in the terminal.

---

## What You'll See

You’ll see output similar to this (snippet):

=== Running Local Chrome Test ===

Article 1:
Spanish Title: Mazón y la nada
Content: El PP, sin líderes ni proyecto en Valencia...
Cover Image Path: None
Translated Header: Mazón and nothingness

...

=== Running BrowserStack Parallel Test ===
[THREAD] Windows_Chrome: Stored 5 articles in result_dict

Results for Windows_Chrome:

Article 1:
Spanish Title: EDITORIAL
Content: EDITORIAL Mazón y la nada ...
Cover Image Path: None
Translated Header: EDITORIAL
...


- **Images are only downloaded** if available; many articles won’t have one, and that’s expected for this news site’s layout.

---

## FAQ & Notes

- **Why so few images?**  
  Only articles with an image in the section listing will be saved—most are text only.
- **About warnings or errors in the logs:**  
  You might see SSL, websocket, or some API warnings when running Selenium in headless/remote/BrowserStack; as long as results are output, everything is functioning as required.
- **Is my .env file safe?**  
  This is ignored by `.gitignore`, so your credentials are never pushed to GitHub.

---

## Submission Checklist

- **This repo**: All code, including this README and the main script.
- **Screenshot**: [Insert your Google Drive screenshot link here]
- **This is a public repo**—viewable by the BrowserStack team.

---

## Author and Notes

Developed by **Sai Revanth**  
Special thanks to the BrowserStack team for the opportunity!

For any issues or questions, just email or DM me.

---

Good luck to all other candidates—and thank you for reviewing my submission!
