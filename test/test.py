import datetime
toDate = datetime.datetime.now()
fromDate = toDate - datetime.timedelta(days = 365 * 2)

while fromDate <= toDate:
  dateFormat = fromDate.strftime("%Y%m%d")
  weekday = fromDate.weekday()
  fromDate = fromDate + datetime.timedelta(days=1)
  # 토요일, 일요일 skip
  if(weekday == 5 or weekday == 6):
    continue

  print(dateFormat + " " + str(weekday))

print("끝.")
