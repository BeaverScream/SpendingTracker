from bs4 import BeautifulSoup # 1

try:
    with open('sample.html', 'r', encoding='utf-8') as file:
        html_content = file.read()
except FileNotFoundError:
    print("Error: 'Sample.html' not found")
    exit()

soup = BeautifulSoup(html_content, 'html.parser') # 3
table = soup.find('table', {'role': 'table'}) # 4
transactions = [] # 9
if table: # 5
    headers = [th.find('span').text.strip() for th in table.find('thead').find_all('th')] # 6
    print(headers)
    tbody = table.find('tbody') # 7
    # if tbody: # 8
        
    #     for row in tbody.find_all('tr', role='row'): # 10
    #         cells = row.find_all('td') # 11
    #         transaction = {} # 12
    #         for i, cell in enumerate(cells): # 13
    #             if i < len(headers): # 14
    #                 transaction[headers[i]] = cell.find('span').text.strip() # 15
    #         transactions.append(transaction) # 16
    #     for trans in transactions: # 17
    #         print(trans) # 18
    # else: # 19
        # print("<tbody> not found.") # 20
else: # 21
    print("Table with role='table' not found.") # 22

print(transactions) # 22