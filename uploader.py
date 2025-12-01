import csv
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# === Google Sheets setup ===
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
# creds and client will be initialized within upload_to_sheet, using the provided keyfile_path

def format_date(date_str):
    """
    Convert date string to 'Mon DD' format.

    Args:
        date_str (str): Input date string in format '%m/%d/%Y' or '%Y-%m-%d'.

    Returns:
        str: Reformatted date string or original if parsing fails.
    """
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%b %d")
        except ValueError:
            continue
    return date_str

def infer_category(detail):
    """
    Guess transaction category based on transaction description.

    Args:
        detail (str): Transaction detail string.

    Returns:
        str: Inferred category ('Restaurant', 'Groceries', 'Transportation', or 'Other Expenses').
    """
    lower_detail = detail.lower()
    if any(keyword in lower_detail for keyword in [
        "mcdonald", "popeyes", "ubereats", "steve's", "doordash", 'tim hortons', 'sushi',
        "hee rae deung", "fantuan", "breka", "big way hot pot", 'ramen'
    ]):
        return "Restaurant"
    elif any(keyword in lower_detail for keyword in [
        "costco", "save on foods", "urban fare", "h-mart", "oddbunch", "chit chat", "wal-mart", 
        "no frills", "hellofresh", "chefs plate"
    ]):
        return "Groceries"
    elif any(keyword in lower_detail for keyword in [
        "impark", "trip", "taxi", "uberone", "compass"
    ]):
        return "Transportation"
    elif any(keyword in lower_detail for keyword in [
        "super save", "esso", "petro", "shell", "husky"
    ]):
        return "Fuel"
    elif any(keyword in lower_detail for keyword in [
        "oldnavy", "carters"
    ]):
        return "Kido"
    else:
        return "Other Expenses"

def find_worksheet(spreadsheet, keyword):
    """
    Search for a worksheet by keyword in its title.

    Args:
        spreadsheet (gspread.Spreadsheet): The spreadsheet object.
        keyword (str): Keyword to match against worksheet titles.

    Returns:
        gspread.Worksheet or None: Matching worksheet or None if not found.
    """
    for ws in spreadsheet.worksheets():
        if keyword.lower() in ws.title.lower():
            return ws
    return None

def prepare_batch_data(rows, bankname, user_type):
    """
    Process CSV rows into formatted data for Google Sheets upload.

    Args:
        rows (list): List of CSV rows.
        bankname (str): Bank name ('tangerine' or 'cibc').
        user_type (int): 1 for you, 2 for your husband.

    Returns:
        list: List of formatted rows (list of cell values).
    """
    batch_data = []
    for row in rows:
        if bankname == "tangerine":
            if len(row) < 5:
                continue
            date_raw = row[0].strip()
            transaction_detail = row[2].strip()
            reward_category = row[3].strip()
            cost_raw = row[4].strip()

            if not date_raw or not transaction_detail or not cost_raw:
                continue
            if 'FREEDOM' in transaction_detail.upper() or \
                'ROGERS' in transaction_detail.upper():
                continue
            if 'PREAUTHORIZED' in transaction_detail.upper():
                continue

            formatted_date = format_date(date_raw)
            reward_match = re.search(r"Rewards earned: ([\d.]+)", reward_category)
            reward = reward_match.group(1) if reward_match else '0'
            cost_value = -float(cost_raw.replace(',', '').replace('$', '').strip())
            formula = f"={abs(cost_value)}-{reward}"
            category = infer_category(transaction_detail)
            
            row_values = [formatted_date, transaction_detail, category]
            if user_type == 1:
                row_values.extend([formula, ''])
            else:
                row_values.extend(['', formula])

            batch_data.append(row_values)

        elif bankname == "cibc":
            if len(row) < 4:
                continue
            date_raw = row[0].strip()
            transaction_detail = row[1].strip()
            cost_raw = row[2].strip()

            if not date_raw or not transaction_detail or not cost_raw:
                continue
            if 'FREEDOM' in transaction_detail.upper() or \
                'ROGERS' in transaction_detail.upper():
                continue

            formatted_date = format_date(date_raw)
            cost_value = -float(cost_raw.replace(',', '').replace('$', '').strip())
            formula = f"={abs(cost_value)}"
            category = infer_category(transaction_detail)

            row_values = [formatted_date, transaction_detail, category]
            if user_type == 1:
                row_values.extend([formula, ''])
            else:
                row_values.extend(['', formula])

            batch_data.append(row_values)

    logger.debug(f"Prepared batch data with {len(batch_data)} rows.")
    return batch_data

def upload_to_sheet(spreadsheet_id, worksheet_keyword, csv_filename, bankname, user_type, keyfile_path):
    """
    Upload parsed CSV data into specified Google Sheet worksheet.

    Args:
        spreadsheet_id (str): ID of the Google Spreadsheet.
        worksheet_keyword (str): Keyword to locate worksheet (e.g., 'Dec').
        csv_filename (str): Path to the CSV file.
        bankname (str): Bank source ('tangerine' or 'cibc').
        user_type (int): 1 = you, 2 = husband.
        keyfile_path (str): Path to the Google service account JSON keyfile.

    Raises:
        ValueError: If worksheet is not found by keyword.
    """
    creds = ServiceAccountCredentials.from_json_keyfile_name(keyfile_path, scope)
    client = gspread.authorize(creds)

    spreadsheet = client.open_by_key(spreadsheet_id)
    worksheet = find_worksheet(spreadsheet, worksheet_keyword)
    if not worksheet:
        logger.error(f"No worksheet found with keyword '{worksheet_keyword}'")
        raise ValueError(f"No worksheet found with keyword '{worksheet_keyword}'")

    with open(csv_filename, mode='r', encoding='utf-8') as file:
        reader = csv.reader(file)
        rows = list(reader)
    logger.info(f"Read {len(rows)} rows from CSV file '{csv_filename}'")

    batch_data = prepare_batch_data(rows, bankname, user_type)

    start_row = 11
    if batch_data:
        end_row = start_row + len(batch_data) - 1
        range_str = f'A{start_row}:E{end_row}'
        worksheet.update(range_name=range_str, values=batch_data, value_input_option='USER_ENTERED')
        logger.info("✅ All applicable rows (excluding FREEDOM) processed and uploaded to Google Sheet.")
    else:
        logger.info("No applicable rows found to upload.")
