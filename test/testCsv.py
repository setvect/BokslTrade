import csv

dct = {'Name': 'John', 'Age': '23', 'Country': 'USA'}

with open('dct.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    for k, v in dct.items():
       writer.writerow([k, v])
