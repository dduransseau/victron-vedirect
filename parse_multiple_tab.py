
from pprint import pprint

with open("victron_output2.csv", "rt", newline="\r\n", encoding="utf8") as csv_file:
    table_dict = dict()
    for line in csv_file:
        if line == '\r\n':
            pprint(table_dict)
            table_dict = dict()
        else:
            l = line.strip().split(",")
            table_dict[l[1]] = l[0]
        # print(line.encode())