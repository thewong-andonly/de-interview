import data_tools
import requests
from datetime import datetime

TODAY = datetime.now()
date_today = TODAY.strftime("%d-%m-%Y")
time_today = TODAY.strftime("%H-%M-%S")
file_suffix = TODAY.strftime("%m-%Y")

sites_dict = {  # 'string of product name': 'string of page to be scraped',

}

# Check for site status before proceeding
for category, url in sites_dict.items():
    try:
        response = requests.get(url)
        status = response.status_code
        if status == 200:
            print(f'{url} status is good.')
        else:
            print(
                f'Error. Status code for {url} is {status} and will not been scraped.')
    except requests.exceptions.ConnectionError:
        print('Connection refused.  Might want to slow down there.')

for product, url in sites_dict.items():

    # Create file name for object
    file_name = data_tools.create_file(product)

    # Constructs a list to check against based on existing data
    existing_product_list = data_tools.existing_items(file_name)

    print(f'Getting data for {product.lower()} @ {url}...\n')

    # Extract data from website and construct list of new items to catalogue
    new_product_list = data_tools.extract(
        3, url, product, existing_product_list)

    # Add new items to database
    if len(new_product_list) >= 1:
        data_tools.save_raw_data(new_product_list, file_name, header_fields=[
            "Product category",
            "Product name",
            "Price (GBP",
            "Date collected"
        ])

        # Process data
        data_tools.process(file_name)
    else:
        print('No new products found.\n')

    # Create a report
    metric_columns = [
        "Report date",
        "Report time",
        "Product category",
        "New products added"
        
    ]

    metric_fields = [
        [date_today,
         time_today,
         product,
         len(new_product_list)]
    ]

    data_tools.metrics(product, metric_columns=metric_columns,
                       metric_fields=metric_fields)


# Close the driver out here.  Closing out driver in other parts of the code results in "too many requests" error.
data_tools.close_driver()
