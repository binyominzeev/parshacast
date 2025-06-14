# main.py

import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import time
import sys
import re
from datetime import datetime, timezone
from email.utils import format_datetime
import ftplib
import json
import os

# --- Configuration ---
BASE_URL = "https://www.yutorah.org/search/rss?q=&f=teacherid:{teacher_id},subcategoryid:{subcategory_id},teacherishidden:0&s=shiurdate%20desc"
RABBIS = [
    {"id": 82281, "name": "Rabbi Yoni Mandelstam"},
    {"id": 80254, "name": "Rabbi Chaim Marcus"},
    {"id": 82280, "name": "Rabbi Jonathan Muskat"},
    {"id": 80288, "name": "Rabbi Avishai David"},
]
SUBCATEGORY_ID = 234553  # Change this if you want a different subcategory

def fetch_lectures():
    lectures = []
    for rabbi in RABBIS:
        url = BASE_URL.format(teacher_id=rabbi["id"], subcategory_id=SUBCATEGORY_ID)
        try:
            response = requests.get(url)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            for item in root.findall(".//item"):
                title = item.findtext("title", "").replace("<![CDATA[", "").replace("]]>", "")
                link = item.findtext("link", "").replace("<![CDATA[", "").replace("]]>", "")
                description = item.findtext("description", "").replace("<![CDATA[", "").replace("]]>", "")
                lectures.append({
                    "rabbi": rabbi["name"],
                    "title": title,
                    "link": link,
                    "description": description,
                })
        except Exception as e:
            print(f"Error fetching/parsing for {rabbi['name']}: {e}")
    return lectures

def fetch_details(lectures, max_count=None):
    print("Fetching details for each lecture...")
    total = len(lectures) if max_count is None else min(len(lectures), max_count)
    for idx, lec in enumerate(lectures[:total]):
        try:
            response = fetch_url_with_retries(lec["link"])
            if not response:
                raise Exception("Failed to fetch page after retries.")

            js_data_match = re.search(r'var lecturePlayerData = (\{.*?\});', response.text, re.DOTALL)
            if not js_data_match:
                print(f"No lecturePlayerData found for: {lec['title']} ({lec['link']})")
                lec["audio_url"] = ""
                lec["date"] = ""
                lec["duration"] = ""
                continue

            js_data = js_data_match.group(1)
            download_url_match = re.search(r'"downloadURL":"(.*?)"', js_data)
            shiur_date_match = re.search(r'"shiurDateUTCDateTime":"(.*?)"', js_data)
            duration_match = re.search(r'"shiurDuration":"(?:(\d+)h )?(\d+)min(?: (\d+)s)? "', js_data)

            download_url = download_url_match.group(1).encode('utf-8').decode('unicode_escape') if download_url_match else ""
            shiur_date = shiur_date_match.group(1) if shiur_date_match else ""

            if duration_match:
                hours = duration_match.group(1) if duration_match.group(1) else "0"
                minutes = duration_match.group(2) if duration_match.group(2) else "0"
                seconds = duration_match.group(3) if duration_match.group(3) else "00"
                formatted_duration = f"{int(hours) * 60 + int(minutes)}:{seconds.zfill(2)}"
            else:
                formatted_duration = ""

            lec["audio_url"] = download_url
            lec["date"] = shiur_date
            lec["duration"] = formatted_duration

        except Exception as e:
            print(f"\nError fetching details for: {lec['title']} ({lec['link']}): {e}")
            lec["audio_url"] = ""
            lec["date"] = ""
            lec["duration"] = ""

        # Progress indicator
        progress = int((idx + 1) / total * 40)
        sys.stdout.write("\r[{}{}] {}/{}".format(
            "#" * progress, " " * (40 - progress), idx + 1, total))
        sys.stdout.flush()
        time.sleep(0.1)  # To avoid hammering the server

    print("\nDetails fetching complete.")

def generate_podcast_xml(lectures, output_path):
    import xml.etree.ElementTree as ET
    from xml.dom import minidom
    from email.utils import format_datetime
    from datetime import datetime

    ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
    ET.register_namespace('itunes', ITUNES_NS)

    # Do NOT set 'xmlns:itunes' here, let ElementTree handle it
    rss = ET.Element('rss', {'version': '2.0'})
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = "My Shiurim Podcast"
    ET.SubElement(channel, 'link').text = "https://binjomin.hu/"
    ET.SubElement(channel, 'description').text = "A collection of parasha from YT / YuT."
    ET.SubElement(channel, 'language').text = "en-us"

    for lec in lectures:
        item = ET.SubElement(channel, 'item')
        ET.SubElement(item, 'title').text = lec.get('title', '')
        ET.SubElement(item, 'link').text = lec.get('audio_url', '')
        ET.SubElement(item, 'guid').text = lec.get('audio_url', '')
        # pubDate: use current timestamp
        now = datetime.now(timezone.utc)
        pub_date = format_datetime(now)
        ET.SubElement(item, 'pubDate').text = pub_date
        # enclosure
        enclosure = ET.SubElement(item, 'enclosure')
        enclosure.set('url', lec.get('audio_url', ''))
        enclosure.set('type', 'audio/mpeg')
        # duration (itunes)
        duration = lec.get('duration', '')
        ET.SubElement(item, '{http://www.itunes.com/dtds/podcast-1.0.dtd}duration').text = duration
        # author
        ET.SubElement(item, 'author').text = lec.get('rabbi', '')

    # Pretty print
    xml_str = ET.tostring(rss, encoding='utf-8')
    pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ", encoding='utf-8')
    with open(output_path, "wb") as f:
        f.write(pretty_xml)

def fetch_url_with_retries(url, retries=3, timeout=5, backoff_factor=1, verbose=False):
    for attempt in range(1, retries + 1):
        try:
            if verbose:
                print(f"Attempt {attempt} of {retries}: Fetching {url} with timeout={timeout}s...")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            if verbose:
                print("Request successful!")
            return response
        except requests.exceptions.RequestException as e:
            if verbose:
                print(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                sleep_duration = backoff_factor * (2 ** (attempt - 1))
                if verbose:
                    print(f"Retrying in {sleep_duration:.2f} seconds...")
                time.sleep(sleep_duration)
            else:
                if verbose:
                    print("All retry attempts failed.")
    return None

def upload_via_ftp(local_file, config_path="ftp_config.json"):
    if not os.path.exists(config_path):
        print(f"FTP config file '{config_path}' not found. Skipping upload.")
        return
    with open(config_path) as f:
        cfg = json.load(f)
    try:
        with ftplib.FTP(cfg["host"]) as ftp:
            ftp.login(cfg["username"], cfg["password"])
            with open(local_file, "rb") as file:
                ftp.storbinary(f"STOR {cfg['remote_path']}", file)
        print(f"Uploaded {local_file} to FTP {cfg['host']}:{cfg['remote_path']}")
    except Exception as e:
        print(f"FTP upload failed: {e}")

def main():
    lectures = fetch_lectures()
    fetch_details(lectures, max_count=3)  # or remove max_count for full run
    output_file = "../data/podcast_feed.xml"
    generate_podcast_xml(lectures, output_file)
    print(f"Podcast XML generated with {len(lectures)} lectures.")
    upload_via_ftp(output_file)

if __name__ == "__main__":
    main()
