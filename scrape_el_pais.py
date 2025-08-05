import os
import time
import threading
import logging
import re
from collections import Counter
import urllib.request
import copy

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from deep_translator import GoogleTranslator

from dotenv import load_dotenv

# --- Load .env if present ---
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scrape_el_pais.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()

class ElPaisScraper:
    def __init__(self, config, result_dict, result_lock):
        self.config = config
        self.driver = None
        self.articles = []
        self.result_dict = result_dict
        self.result_lock = result_lock

    def initialize_driver(self):
        if self.config.get('browserstack', False):
            options = webdriver.ChromeOptions()
            for key in ['os', 'os_version', 'browser', 'browser_version', 'name']:
                if key in self.config:
                    options.set_capability(key, self.config[key])
            if 'device' in self.config:
                options.set_capability('device', self.config['device'])
                options.set_capability('real_mobile', 'true')
            options.set_capability('browserstack.local', 'false')
            options.set_capability('browserstack.debug', 'true')
            options.set_capability('browserstack.console', 'verbose')
            options.set_capability('browserstack.networkLogs', 'true')
            bs_user = os.getenv('BROWSERSTACK_USERNAME')
            bs_key = os.getenv('BROWSERSTACK_ACCESS_KEY')
            hub_url = f'https://{bs_user}:{bs_key}@hub-cloud.browserstack.com/wd/hub'
            self.driver = webdriver.Remote(
                command_executor=hub_url,
                options=options
            )
        else:
            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)

    def translate_text(self, text, source='es', target='en'):
        for attempt in range(3):
            try:
                return GoogleTranslator(source=source, target=target).translate(text)
            except Exception as e:
                logger.warning(f"Translation failed (attempt {attempt+1}): {e}")
                time.sleep(1)
        return text

    def scrape_articles(self):
        try:
            self.driver.implicitly_wait(10)
        except Exception as e:
            logger.warning(f"Could not set implicit wait: {e}")
        self.driver.get("https://elpais.com/opinion/")
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.XPATH, "//html[@lang='es' or @lang='es-ES']"))
            )
        except Exception as e:
            logger.warning(f"Could not verify Spanish language: {e}")
        for _ in range(3):
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.7);")
            time.sleep(1.0)
        articles = self.driver.find_elements(By.TAG_NAME, "article")[:10]
        logger.info(f"{self.config['name']}: Found {len(articles)} articles")
        collected = 0
        for idx, article in enumerate(articles):
            try:
                # More robust extraction logic for all browsers/sessions
                title = ""
                try:
                    title = article.find_element(By.CSS_SELECTOR, "h2").text.strip()
                except Exception:
                    pass
                if not title:
                    try:
                        title = article.find_element(By.TAG_NAME, "h2").text.strip()
                    except Exception:
                        pass
                if not title:
                    try:
                        title = article.get_attribute('innerText').split('\n')[0].strip()
                    except Exception:
                        pass
                if not title or title == "":
                    continue

                content = ""
                try:
                    ps = article.find_elements(By.TAG_NAME, "p")
                    if ps:
                        content = " ".join([p.text for p in ps if p.text.strip()])
                except Exception:
                    pass
                if not content:
                    try:
                        content = article.text.strip()
                    except Exception:
                        pass
                if not content:
                    try:
                        content = article.get_attribute('innerText').strip()
                    except Exception:
                        pass

                img_url = None
                try:
                    img_elem = article.find_element(By.CSS_SELECTOR, "img")
                    img_url = img_elem.get_attribute("src")
                except Exception:
                    pass
                img_path = None
                if img_url and img_url.startswith("http"):
                    img_dir = f"article_images_{self.config['name']}"
                    os.makedirs(img_dir, exist_ok=True)
                    img_path = f"{img_dir}/article_{collected+1}.jpg"
                    try:
                        urllib.request.urlretrieve(img_url, img_path)
                    except Exception as e:
                        logger.warning(f"Failed saving image: {e}")
                        img_path = None

                self.articles.append({
                    'original_title': title,
                    'content': content,
                    'img_path': img_path,
                })
                collected += 1
                logger.info(f"{self.config['name']}: Processed article {collected}: {title[:50]}")
                if collected == 5:
                    break
            except Exception as e:
                logger.warning(f"Error parsing article: {e}")

    def analyze_headers(self, translated_titles):
        all_words = []
        for title in translated_titles:
            words = re.findall(r'\b\w+\b', title.lower())
            all_words.extend(words)
        word_counts = Counter(all_words)
        repeated = {word: count for word, count in word_counts.items() if count > 2}
        return repeated

    def run(self):
        try:
            self.initialize_driver()
            self.scrape_articles()
            articles_copy = []
            for article in self.articles:
                try:
                    article['translated_title'] = self.translate_text(article['original_title'])
                except Exception as e:
                    logger.warning(f"{self.config['name']}: Translation failed: {e}")
                articles_copy.append(copy.deepcopy(article))
            translated_titles = [a['translated_title'] for a in articles_copy]
            repeated = self.analyze_headers(translated_titles)
            with self.result_lock:
                self.result_dict[self.config['name']] = {
                    'articles': articles_copy,
                    'repeated': repeated
                }
                # Debug print
                print(f"[THREAD] {self.config['name']}: Stored {len(articles_copy)} articles in result_dict")
        finally:
            if self.driver:
                self.driver.quit()
                logger.info(f"{self.config['name']}: Driver closed")

def run_all_parallel(configs):
    results = {}
    result_lock = threading.Lock()
    threads = []
    for cfg in configs:
        scraper = ElPaisScraper(cfg, results, result_lock)
        thread = threading.Thread(target=scraper.run)
        threads.append(thread)
        thread.start()
        time.sleep(1)
    for t in threads:
        t.join()
    return results

if __name__ == '__main__':
    local_config = [{
        'browserstack': False,
        'name': 'Local_Chrome'
    }]
    browserstack_configs = [
        {
            'browserstack': True,
            'os': 'Windows', 'os_version': '10',
            'browser': 'Chrome', 'browser_version': 'latest',
            'name': 'Windows_Chrome'
        },
        {
            'browserstack': True,
            'os': 'OS X', 'os_version': 'Ventura',
            'browser': 'Firefox', 'browser_version': 'latest',
            'name': 'Mac_Firefox'
        },
        {
            'browserstack': True,
            'device': 'iPhone 14', 'os_version': '16',
            'browser': 'Safari', 'name': 'iPhone_Safari'
        },
        {
            'browserstack': True,
            'device': 'Samsung Galaxy S22', 'os_version': '12.0',
            'browser': 'Chrome', 'name': 'Samsung_Chrome'
        },
        {
            'browserstack': True,
            'os': 'Windows', 'os_version': '10',
            'browser': 'Edge', 'browser_version': 'latest',
            'name': 'Windows_Edge'
        }
    ]

    print("\n=== Running Local Chrome Test ===")
    local_results = run_all_parallel(local_config)
    for name, results in local_results.items():
        print(f"\nResults for {name}:")
        if not results['articles']:
            print("No articles found (possibly BrowserStack did not return results in time).")
            continue
        for idx, art in enumerate(results['articles'], 1):
            print(f"\nArticle {idx}:")
            print(f"Spanish Title: {art['original_title']}")
            print(f"Content: {art['content'][:100]}...")
            print(f"Cover Image Path: {art['img_path']}")
            print(f"Translated Header: {art['translated_title']}")
        if results['repeated']:
            print("\nRepeated Words in English Headers (more than twice):")
            for word, count in results['repeated'].items():
                print(f"{word}: {count}")

    print("\n=== Running BrowserStack Parallel Test ===")
    bs_results = run_all_parallel(browserstack_configs)
    for name, results in bs_results.items():
        print(f"\nResults for {name}:")
        if not results['articles']:
            print("No articles found (possibly BrowserStack did not return results in time).")
            continue
        for idx, art in enumerate(results['articles'], 1):
            print(f"\nArticle {idx}:")
            print(f"Spanish Title: {art['original_title']}")
            print(f"Content: {art['content'][:100]}...")
            print(f"Cover Image Path: {art['img_path']}")
            print(f"Translated Header: {art['translated_title']}")
        if results['repeated']:
            print("\nRepeated Words in English Headers (more than twice):")
            for word, count in results['repeated'].items():
                print(f"{word}: {count}")
