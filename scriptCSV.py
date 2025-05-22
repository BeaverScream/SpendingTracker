import csv
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# === Google Sheets setup ===
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('sample-25a27-e4c1004f429c.json', scope)
client = gspread.authorize(creds)

# === User inputs ===
keyword = input("Enter month keyword (e.g. 'Dec'): ")
filename = input("Enter CSV filename (e.g. 'World MastercardDec2024.csv'): ")
bankname = input("Enter the bank name (e.g. 'tangerine' or 'cibc'): ").strip().lower()

while True:
    try:
        user_type = int(input("Enter user type (1 or 2): ").strip())
        if user_type in [1, 2]:
            break
        else:
            print("Please enter 1 or 2.")
    except ValueError:
        print("Invalid input. Please enter a number (1 or 2).")

# === Spreadsheet setup ===
spreadsheet_id = '1k3JZUGIxrI4QtqJjshUlMN3_ixoKegOVs8W_4tEr2y8'
spreadsheet = client.open_by_key(spreadsheet_id)

# === Find worksheet that contains a keyword in its title ===
worksheet = None
for ws in spreadsheet.worksheets():
    if keyword.lower() in ws.title.lower():
        worksheet = ws
        break

if not worksheet:
    raise ValueError(f"No worksheet found with keyword '{keyword}'")

# === Read CSV file ===
with open(filename, mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    rows = list(reader)

# === Helper functions ===
def format_date(date_str):
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%b %d")
        except ValueError:
            continue
    return date_str

def infer_category(detail):
    lower_detail = detail.lower()
    if any(keyword in lower_detail for keyword in [
        "mcdonald", "popeyes", "ubereats", "steve's", "doordash",
        "hee rae deung", "fantuan", "breka", "big way hot pot"
    ]):
        return "Restaurant"
    elif any(keyword in lower_detail for keyword in [
        "costco", "save on foods", "urban fare", "h-mart", "oddbunch", "chit chat"
    ]):
        return "Groceries"
    elif any(keyword in lower_detail for keyword in [
        "impark", "trip", "taxi", "uberone", "compass"
    ]):
        return "Transportation"
    else:
        return "Other Expenses"

# === Start processing ===
start_row = 11
current_row = start_row

# Find first empty row in column A
while worksheet.acell(f"A{current_row}").value:
    current_row += 1

batch_data = []

for row in rows:
    if bankname == "tangerine":
        if len(row) < 5:
            continue

        date_raw = row[0].strip()
        payment_type = row[1].strip()
        transaction_detail = row[2].strip()
        reward_category = row[3].strip()
        cost_raw = row[4].strip()

        if not date_raw or not transaction_detail or not cost_raw:
            continue
        if 'FREEDOM' in transaction_detail.upper() or 'PREAUTHORIZED' in transaction_detail.upper():
            continue

        formatted_date = format_date(date_raw)

        reward_match = re.search(r"Rewards earned: ([\d.]+)", reward_category)
        category_match = re.search(r"Category: ([\w &]+)", reward_category)
        reward = reward_match.group(1) if reward_match else '0'
        category = category_match.group(1) if category_match else ''

        cost_value = -float(cost_raw.replace(',', '').replace('$', '').strip())
        formula = f"={abs(cost_value)}-{reward}"

        row_data = [formatted_date, transaction_detail, category]
        if user_type == 1:
            row_data.extend([formula, ''])  # D=amount, E=empty
        else:
            row_data.extend(['', formula])  # D=empty, E=amount

        batch_data.append(row_data)

    elif bankname == "cibc":
        if len(row) < 3:
            continue

        date_raw = row[0].strip()
        transaction_detail = row[1].strip()
        cost_raw = row[2].strip()

        if not date_raw or not transaction_detail or not cost_raw:
            continue
        if 'FREEDOM' in transaction_detail.upper():
            continue

        formatted_date = format_date(date_raw)
        cost_value = -float(cost_raw.replace(',', '').replace('$', '').strip())
        formula = f"={abs(cost_value)}"
        category = infer_category(transaction_detail)

        row_data = [formatted_date, transaction_detail, category]
        if user_type == 1:
            row_data.extend([formula, ''])  # D=amount, E=empty
        else:
            row_data.extend(['', formula])  # D=empty, E=amount

        batch_data.append(row_data)

# === Perform batch update ===
if batch_data:
    end_row = current_row + len(batch_data) - 1
    range_str = f"A{current_row}:E{end_row}"
    # worksheet.update(range_str, batch_data)
    # worksheet.update(values=batch_data, range_name=range_str)
    worksheet.update(range_name=range_str, values=batch_data, value_input_option='USER_ENTERED')

    print("✅ All applicable rows (excluding FREEDOM) processed and uploaded to Google Sheet.")
else:
    print("⚠️ No valid data to upload.")