#!/usr/bin/env python3
import re
import subprocess
import time
from termcolor import colored
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import sys
from datetime import datetime
import math

VERSION = "v1.2"

def print_banner():
    banner = """"""
    print(banner)
    animated_text("Project ESQLi Error-Based Tool", 'blue')

def animated_text(text, color='white', speed=0):
    for char in text:
        sys.stdout.write(colored(char, color))
        sys.stdout.flush()
        time.sleep(speed)
    print()

def random_delay():
    if args.silent:
        time.sleep(0.05)  # Reduced from 60/12 seconds to 0.05 seconds
    else:
        base_delay = 0.2  # Reduced delay for faster scans
        jitter = random.uniform(0.1, 0.3)
        time.sleep(base_delay * jitter)

# Create the argument parser and add arguments
parser = argparse.ArgumentParser(description="SQLi Error-Based Tool")
parser.add_argument("-u", "--urls", required=True, help="Provide a URLs list for testing", type=str)
parser.add_argument("-p", "--payloads", required=True, help="Provide a list of SQLi payloads for testing", type=str)
parser.add_argument("-s", "--silent", action="store_true", help="Rate limit to 12 requests per second")
parser.add_argument("-f", "--fast", action="store_true", help="Use multi-threading for faster scanning")
parser.add_argument("-o", "--output", help="File to save only positive results")
parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {VERSION}", help="Display version information and exit")

args = parser.parse_args()

# Check if required arguments are missing
if not args.urls or not args.payloads:
    parser.error("the following arguments are required: -u/--urls, -p/--payloads")

print_banner()

with open(args.urls, 'r') as f:
    urls = f.read().splitlines()

with open(args.payloads, 'r') as f:
    payloads = f.read().splitlines()

# Randomize the order of URLs
random.shuffle(urls)

# User agents list
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.1.2 Safari/537.36",
    # Add more agents as needed
]

sql_errors = [
    "Syntax error", "Fatal error", "MariaDB", "corresponds", "Database Error",
    "syntax", "/usr/www", "public_html", "database error", "on line", "mysql_", "MySQL", "PSQLException"
]

total_requests = len(urls) * len(payloads) * max(url.count('&') + 1 for url in urls)
progress = 0
start_time = time.time()

# Determine output file name
output_file = args.output if args.output else f"positive_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def scan_url(url, payload):
    base_url, query_string = url.split('?', 1) if '?' in url else (url, '')
    pairs = query_string.split('&')

    payload = payload.replace("'", "%27")
    for i in range(len(pairs)):
        modified_pairs = pairs.copy()
        if '=' in modified_pairs[i]:
            key, value = modified_pairs[i].split('=', 1)
            modified_pairs[i] = f"{key}={payload}"
        url_modified = f"{base_url}?{'&'.join(modified_pairs)}"
        user_agent = random.choice(user_agents)  # Randomly choose a user agent
        command = ['curl', '-s', '-i', '--url', url_modified, '-A', user_agent]  # Add user agent to command
        output_bytes = None

        try:
            output_bytes = subprocess.check_output(command, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            pass

        if output_bytes is not None:
            output_str = output_bytes.decode('utf-8', errors='ignore')
            sql_matches = [error for error in sql_errors if error in output_str]
            if sql_matches:
                message = f"\n{colored('SQL ERROR FOUND', 'white')} ON {colored(url_modified, 'red', attrs=['bold'])} with payload {colored(payload, 'white')}"
                print(message)
                for match in sql_matches:
                    print(colored(" Match Words: " + match, 'cyan'))
                # Immediately save the positive result
                with open(output_file, 'a') as file:
                    file.write(url_modified + '\n')

        global progress
        progress += 1

# Optimize progress update rate
def print_progress():
    elapsed_seconds = time.time() - start_time
    remaining_seconds = (total_requests - progress) * (elapsed_seconds / progress) if progress > 0 else 0
    remaining_hours = int(remaining_seconds // 3600)
    remaining_minutes = int((remaining_seconds % 3600) // 60)
    percent_complete = round(progress / total_requests * 100, 2)
    if progress % 10 == 0:  # Update progress every 10 URLs to reduce print overhead
        print(f"{colored('Progress:', 'blue')} {progress}/{total_requests} ({percent_complete}%) - {remaining_hours}h:{remaining_minutes:02d}m")

# Batch processing to limit the number of threads
def batch_process(urls, payloads, batch_size=10):
    total_batches = math.ceil(len(urls) / batch_size)
    for i in range(total_batches):
        batch_urls = urls[i * batch_size:(i + 1) * batch_size]
        with ThreadPoolExecutor(max_workers=10) as executor:  # Safe number of threads
            futures = [executor.submit(scan_url, url, payload) for url in batch_urls for payload in payloads]
            for future in as_completed(futures):
                print_progress()

# Call the batch processing function
if args.fast:
    batch_process(urls, payloads, batch_size=10)  # Adjust batch size if needed
else:
    for url in urls:
        for payload in payloads:
            scan_url(url, payload)
            print_progress()

end_time = time.time()
total_time = end_time - start_time
print("Scanning completed.")
print(f"Total time taken: {total_time:.2f} seconds")
