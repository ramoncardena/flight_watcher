import sys
from datetime import datetime

# from seleniumwire import webdriver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.common.exceptions import TimeoutException
from webdriver_manager.firefox import GeckoDriverManager

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# proxy_list = [
#     {'http': '47.251.122.81:8888', 'https': '47.251.122.81:8888'},
#     {'http': '203.74.125.18:8888', 'https': '203.74.125.18:8888'},
#     {'http': '179.96.28.58:80', 'https': '179.96.28.58:80'},
#     {'http': '13.38.153.36:80', 'https': '13.38.153.36:80'},
#     {'http': '13.37.59.99:3128', 'https': '13.37.59.99:3128'},
#     {'http': '13.36.87.105:3128', 'https': '13.36.87.105:3128'},
#     {'http': '35.72.118.126:80', 'https': '35.72.118.126:80'},
#     {'http': '3.122.84.99:3128', 'https': '3.122.84.99:3128'},
#     {'http': '46.51.249.135:3128', 'https': '46.51.249.135:3128'},
#     {'http': '52.196.1.182:80', 'https': '52.196.1.182:80'},
#     {'http': '3.78.92.159:3128', 'https': '3.78.92.159:3128'},
#     {'http': '99.80.11.54:3128', 'https': '99.80.11.54:3128'},
#     {'http': '8.215.105.127:7777', 'https': '8.215.105.127:7777'},
#     {'http': '3.141.217.225:80', 'https': '3.141.217.225:80'},
#     {'http': '51.68.175.56:1080', 'https': '51.68.175.56:1080'},
#     {'http': '113.160.133.32:8080', 'https': '113.160.133.32:8080'},
#     {'http': '172.233.78.254:7890', 'https': '172.233.78.254:7890'},
#     {'http': '31.40.248.2:8080', 'https': '31.40.248.2:8080'},
#     {'http': '216.229.112.25:8080', 'https': '216.229.112.25:8080'},
#     {'http': '129.154.225.163:8100', 'https': '129.154.225.163:8100'}
# ]

def send_email(flight_data, destination):
    recipient_email = "info@ramoncardena.com"
    sender_email = "info@ramoncardena.com"  # Replace with your email
    password = "Huitzil0p0chtli$"  # Use an app password for Gmail

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = f"BCN-{destination}: Flight Prices Summary"
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
    body = f"BCN - {destination} Prices Summary ({timestamp})\n\n"
    for flight in flight_data:
        body += f"Price: {flight['price']}€ ({flight['company']})\nOutbound: {flight['departure_date']} at {flight['departure_time']}\nInbound: {flight['return_date']} at {flight['return_time']}\n\n"

    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.migadu.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(message)
        print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")


def setup_driver():
    firefox_options = webdriver.FirefoxOptions()
    firefox_options.add_argument("--headless")
    # return webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=firefox_options, seleniumwire_options= {'proxy': proxy_list[0]})
    return webdriver.Firefox(
        service=Service(GeckoDriverManager().install()), options=firefox_options
    )


def search_flight(driver, destination, departure_day, return_day):

    url = f"https://www.kayak.es/flights/BCN,nearby-{destination}/2025-09-{departure_day}-flexible-2days/2025-09-{return_day}-flexible-2days?fs=fdDir=true;stops=~0&ucs=1cpbtj0&sort=price_a"

    driver.get(url)

    print(f"Searching for flights to {destination}...")


def handle_privacy_popup(driver):
    try:
        # Wait for the "Rechazar todo" button to become clickable
        wait = WebDriverWait(driver, 10)
        accept_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(., 'Rechazar todo')]")
            )
        )
        accept_button.click()
    except Exception as e:
        print(f"An error occurred while handling the privacy popup: {e}")


def check_results(driver):
    try:
        # Scroll down to ensure all content is loaded
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        # Wait for flight results after handling the popup
        wait = WebDriverWait(driver, 30)
        results = wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "Fxw9")))

        # print("Flight results found!")
        return results
    except Exception as e:
        print(f"An error occurred while waiting for flight results: {e}")
        return None


def extract_prices(results):
    price_company_list = []
    flights = results.find_elements(By.CLASS_NAME, "Fxw9-result-item-container")

    for flight in flights:
        try:
            # Extract price.
            price_element = flight.find_element(
                By.CSS_SELECTOR, "[class*='f8F1-price-text']"
            )
            price = int(price_element.text.replace("€", "").replace(".", "").strip())

            # Extract company.
            company_img = flight.find_element(By.CSS_SELECTOR, "img[alt]")
            company = company_img.get_attribute("alt")

            # Extract flight departure and return times
            times = flight.find_elements(By.CSS_SELECTOR, ".vmXl-mod-variant-large")

            # Extract flight dates.
            dates = flight.find_elements(By.CSS_SELECTOR, ".tdCx-bottom")

            departure_date = dates[0].text
            deparure_time = times[0].text
            return_date = dates[1].text
            return_time = times[1].text

            price_company_list.append(
                {
                    "price": price,
                    "company": company,
                    "departure_date": departure_date,
                    "departure_time": deparure_time,
                    "return_date": return_date,
                    "return_time": return_time,
                }
            )
        except Exception as e:
            continue

    # Sort the list by price
    price_company_list.sort(key=lambda x: x["price"])

    return price_company_list

def wait_for_results(driver, timeout=30):
    try:
        def at_least_10_results(driver):
            elements = driver.find_elements(By.CLASS_NAME, "Fxw9-result-item-container")
            return len(elements) >= 10

        wait = WebDriverWait(driver, timeout)
        wait.until(at_least_10_results)
        # print(f"Found at least 10 flight results.")
    except TimeoutException:
        print(f"Timeout: Less than 10 flight results found after {timeout} seconds.")

def main(destination="ATL", departure_day=8, return_day=30):
    try:
        driver = setup_driver()

        # Start searching for flights.
        search_flight(driver, destination, departure_day, return_day)

        # Handle privacy popup
        handle_privacy_popup(driver)

        # Add wait.
        wait_for_results(driver)

        # Check for flight results.
        results = check_results(driver)

        price_company_list = extract_prices(results)

        if price_company_list:
            print("\nFlight Prices and Companies:")
            for index, item in enumerate(price_company_list[:5], 1):
                print(f"{index}. {item['company']} - {item['price']}€")
                print(f"{item['departure_date']}: {item['departure_time']}")
                print(f"{item['return_date']}: {item['return_time']}")

            # Send email with flight data
            send_email(price_company_list[:6], destination)
        else:
            print("No valid flight data could be extracted.")

        driver.quit()
    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    script_name = sys.argv[0]
    args = sys.argv[1:]  # All arguments after the script name

    # Default values for optional parameters
    destination = "MIA"
    departure_day = "08"
    return_day = "30"

    if args:  # If at least one argument is provided beyond the script name
        destination_arg = args[0].upper()
        if destination_arg == destination:
            pass  # Already matches default, no change needed
        else:
            destination = destination_arg

    if len(args) >= 2:  # Check for departure day
        departure_day_arg = args[1]
        if departure_day_arg != departure_day:
            departure_day = departure_day_arg

    if len(args) >= 3:  # Check for return day
        return_day_arg = args[2]
        if return_day_arg != return_day:
            return_day = return_day_arg

    main(destination, departure_day, return_day)
