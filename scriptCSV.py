import csv
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# === Google Sheets setup ===
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name('sample-25a27-e4c1004f429c.json', scope)
client = gspread.authorize(creds)

# === Spreadsheet setup ===
spreadsheet_id = '1k3JZUGIxrI4QtqJjshUlMN3_ixoKegOVs8W_4tEr2y8'  # hardcoded for test
spreadsheet = client.open_by_key(spreadsheet_id)

# === Find worksheet that contains a keyword in its title ===
keyword = 'Dec'
worksheet = None
for ws in spreadsheet.worksheets():
    if keyword.lower() in ws.title.lower():
        worksheet = ws
        break

if not worksheet:
    raise ValueError(f"No worksheet found with keyword '{keyword}'")

# === Read CSV file ===
filename = 'World MastercardDec2024.csv'
with open(filename, mode='r', encoding='utf-8') as file:
    reader = csv.reader(file)
    rows = list(reader)

# === Helper function ===
def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
        return date_obj.strftime("%b %d")  # 'Apr 06'
    except Exception:
        return date_str  # return original if formatting fails

# === Start processing ===
start_row = 11
current_row = start_row
freedom_row = 7  # Always paste FREEDOM at row 7 in column M (i.e. M7)

for row in rows:
    if len(row) < 5:
        continue  # skip malformed rows

    date_raw = row[0].strip()
    payment_type = row[1].strip()
    transaction_detail = row[2].strip()
    reward_category = row[3].strip()
    cost_raw = row[4].strip()

    if not date_raw or not transaction_detail or not cost_raw:
        continue

    if 'PREAUTHORIZED' in transaction_detail.upper():
        continue

    # === Format values ===
    formatted_date = format_date(date_raw)

    # Extract reward and category
    reward_match = re.search(r"Rewards earned: ([\d.]+)", reward_category)
    category_match = re.search(r"Category: ([\w &]+)", reward_category)
    reward = reward_match.group(1) if reward_match else '0'
    category = category_match.group(1) if category_match else ''

    # Flip sign of amount
    cost_value = -float(cost_raw.replace(',', '').replace('$', '').strip())
    formula = f"={abs(cost_value)}-{reward}"

    if 'FREEDOM' in transaction_detail.upper():
        worksheet.update_acell(f'M{freedom_row}', formatted_date)
        worksheet.update_acell(f'N{freedom_row}', transaction_detail)
        worksheet.update_acell(f'O{freedom_row}', "Telecommunication")
        worksheet.update_acell(f'P{freedom_row}', formula)
        continue

    # Write values to next available row starting at A11
    while worksheet.acell(f"A{current_row}").value:
        current_row += 1

    worksheet.update_acell(f'A{current_row}', formatted_date)
    worksheet.update_acell(f'B{current_row}', transaction_detail)
    worksheet.update_acell(f'C{current_row}', category)
    worksheet.update_acell(f'D{current_row}', formula)

# Write values to next available row starting at A11
while worksheet.acell(f"A{current_row}").value:
    current_row += 1

print("✅ All applicable rows processed and uploaded to Google Sheet.")
