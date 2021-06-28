users = [
    {"mail": "gregorythomas@gmail.com", "name": "Brett Holland", "sex": "M"},
    {"mail": "hintoncynthia@hotmail.com", "name": "Madison Martinez", "sex": "F"},
    {"mail": "wwagner@gmail.com", "name": "Michael Jenkins", "sex": "M"},
    {"mail": "daniel79@gmail.com", "name": "Karen Rodriguez", "sex": "F"},
    {"mail": "ujackson@gmail.com", "name": "Amber Rhodes", "sex": "F"},
]


def conver_to_name(user):
    first, last = user["name"].split()
    return {"first": first, "last": last}


for name in map(conver_to_name, users):
    print(name)

print("-----------------")

for mail in map(lambda u: "남" if u["sex"] == "M" else "여", users):
    print(mail)

aa = map(lambda u: u["mail"], users)
print(aa)

bb = list(map(lambda u: u["mail"], users))
print(bb)


cc = [user["mail"] for user in users]
print(cc)
