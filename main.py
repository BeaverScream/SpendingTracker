import argparse
from uploader import upload_to_sheet

def parse_args():
    parser = argparse.ArgumentParser(description="Upload bank CSV data to Google Sheets")
    parser.add_argument('--spreadsheet_id', type=str, required=True, help="Google Spreadsheet ID")
    parser.add_argument('--keyword', type=str, required=True, help="Worksheet keyword (e.g. 'Dec')")
    parser.add_argument('--filename', type=str, required=True, help="CSV filename")
    parser.add_argument('--bankname', type=str, choices=['tangerine', 'cibc'], required=True, help="Bank name")
    parser.add_argument('--usertype', type=int, choices=[1, 2], required=True, help="User type (1 or 2)")
    return parser.parse_args()

def main():
    args = parse_args()
    upload_to_sheet(args.spreadsheet_id, args.keyword, args.filename, args.bankname.lower(), args.usertype)

if __name__ == "__main__":
    main()