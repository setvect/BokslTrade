num = 10000000
print("{num:,}".format(num=num))

num = 13553.1456567
print("{num:0,.2f}".format(num=num))

a = None

print(a is not None)


num = 3

print("홀수" if num % 2 else "짝수")

obj = None

print("비여있음" if obj is None else "있음")

print()

arr = [2, 7, 10]
for idx, val in enumerate(arr):
    print(idx, val)
