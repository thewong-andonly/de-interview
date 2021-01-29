from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import os
import csv
import pandas as pd
pd.options.mode.chained_assignment = None

DRIVER = webdriver.Chrome()
DRIVER.minimize_window()

TODAY = datetime.now()
date_today = TODAY.strftime("%d-%m-%Y")
time_today = TODAY.strftime("%H-%M-%S")
date_and_time_today = date_today + '-' + time_today
file_suffix = TODAY.strftime("%m-%Y")

# This holds all of of the functions used in main py
# This has been sorted by function name alphabetically.


def close_driver():
    """
    Closes the webdriver.
    """
    DRIVER.quit()


def create_file(product_category):
    """
    Creates a unique file name on a monthly rotation
    e.g. website-product-here-01-2021.csv

    Params:
        product_category (str): name of the category being scraped.

    Returns:
        file_name (str):  name of the resultant file.
    """
    product_split = product_category.lower().split()
    product_formatted = '-'.join(product_split)

    file_name =  # (website goes here)'-'+product_formatted+'-'+file_suffix+'.csv'
    return file_name


def existing_items(file_name):
    """
    Checks if a directory for the product exists.  If so, creates a list of items which can be crosschecked against webscraped items.
    Params:
        input_dictionary (dict): 
    """
    product_list = []
    if os.path.isfile(file_name):
        print('Existing directory found.  Loading...')
        with open(file_name, 'r') as database:
            reader = csv.reader(database)
            for entry in reader:
                product_list.append(entry[1])
        print('Existing directory loaded.\n')
    else:
        print(
            f'No previous directory found. New directory to be created: {file_name}\n')
        product_list = []  # Blank item list if no directory exists

    return product_list


def extract(number_of_pages,
            url_to_scrape,
            product,
            list_of_existing):
    """
    Scrapes data from the web page and compares it against a list_of_existing products.
    If the data is not in the list_of_existing products, it is added to list_of_new which is 
    returned at the end.

    Params:
        number_of_pages (int): number of pages to scrape.

        url_to_scrape (str): target url to scrape.

        product (str): product category being scraped.

        list_of_existing (list of str): list of existing products for function to compare against.

    Returns:
        list_of_new (list of list of str): list of new products.
    """

    list_of_new = []

    for i in range(1, number_of_pages):
        full_url_to_scrape = url_to_scrape + '?page=' + (str(i))
        print(f'Scraping from {full_url_to_scrape}')
        DRIVER.get(full_url_to_scrape)

        # Implicit wait for all page elements to load
        WebDriverWait(DRIVER, 20).until(EC.visibility_of_all_elements_located(
            (By.XPATH, '//a[@class="cept-tt thread-link linkPlain thread-title--list"]')))  # wait for all products to load
        page_items = DRIVER.find_elements_by_xpath(
            '//a[@class="cept-tt thread-link linkPlain thread-title--list"]')  # All products has this class name
        page_price = DRIVER.find_elements_by_xpath(
            "//span[@class='thread-price text--b cept-tp size--all-l size--fromW3-xl']")  # All prices have this class name

        # Looping over lists
        for item, price in zip(page_items, page_price):
            parse_title = item.get_attribute('title')

            # Product name
            product_name = parse_title

            # Item price
            parse_price = price.text.split('£')[1].replace(',', '')
            product_price = parse_price

            # Product category
            product_category = product

            # Check for duplicates
            if (product_name not in list_of_existing) and (product_name not in list_of_new):
                list_of_new.append([
                    product_category,
                    product_name,
                    product_price,
                    date_today
                ])
    return list_of_new


def metrics(product,
            metric_columns,
            metric_fields):
    """
    Produces metrics when the program is run in a .csv format.
    Uses pandas to convert ':' in the Report time column to '-'

    Params:
        product: product category

        metric_columns: column names for report

        metric fields: data to be written in the report.
    """
    product_split = product.lower().split()
    product_formatted = '-'.join(product_split)

    report_file_name = product_formatted+'-'+file_suffix+'-'+'report.csv'
    metric_report_exists = os.path.isfile(report_file_name)
    with open(report_file_name, 'a') as database:
        if not metric_report_exists:
            print('No prior metric report found. Creating new metric report...')
            # Header names
            writer = csv.DictWriter(database, fieldnames=metric_columns)
            writer.writeheader()
        print('Adding data to metric report.\n')
        writer = csv.writer(database)
        for data in metric_fields:
            writer.writerow(data)

    df = pd.read_csv(report_file_name)
    for entry in df["Report time"]:
        df["Report time"] = df["Report time"].str.replace('-', ':')
    df.to_csv(report_file_name, index=False)

    print(f'Report for {product.lower()} completed. Saved as {report_file_name}.\n')


def process(file_name):
    """
    Processes the original file in Pandas by adding a vendor column, parsing the text, splitting at the @ symbol to create vendor values.
    Also parses the date into separate columns of Day, Month, Year.
    Produces a processed file called processed+file_name.

    Params:
        file_name (str): File to be cleaned.

    """
    print(f'Processing data for {file_name}...')
    processed_file_name = 'processed-' + file_name
    processed_file_exists = os.path.isfile(processed_file_name)
    df = pd.read_csv(file_name, encoding="cp1252")
    df.insert(2, 'Vendor', None)
    i = 0
    # Isolates vendors, may have edge cases.
    for entry in df['Product name']:
        separators = [' at ',  '@', ' via ', ' VIA ']
        for separator in separators:
            if separator in entry:
                entry = entry.replace(separator, ' @ ')
                new_entry = entry.split('@')
                product_name = new_entry[0]
        if len(new_entry) > 1:
            vendor = new_entry[-1]
        else:
            vendor = 'EDGE CASE HERE'
        df['Vendor'][i] = vendor
        df['Product name'][i] = product_name
        i += 1

    df[['Day', 'Month', 'Year']] = df['Date collected'].str.split(
        '-', 3, expand=True)

    df.to_csv(processed_file_name, encoding="cp1252", index=False)
    print('Data processed.')


def save_raw_data(input_list,
                  file_name,
                  header_fields):
    """
    Writes the data from input_list to a .csv file named as file_name.
    If no existing file appears, a new one will be created with the headers from header_fields.

    Params:
        input_list (list of str): list of items to be saved.

        file_name (str): name of the .csv file.

        header_fields (list of str): names of the columns in the .csv file.
    """
    print(f'Adding {len(input_list)} item(s) to database...\n')
    database_exists = os.path.isfile(file_name)
    with open(file_name, 'a', newline='') as database:
        if not database_exists:
            # Header names
            fields = header_fields
            writer = csv.DictWriter(database,
                                    fieldnames=fields)
            writer.writeheader()
        writer = csv.writer(database)
        for data in input_list:
            writer.writerow(data)
    print('Finished adding new products.\n')