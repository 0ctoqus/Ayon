def get_height(n):
    if n % 8 == 0 and n > 0:
        n = n - 1
    return n / 8


print(get_height(0))
print(get_height(8))
print(get_height(9))
print(get_height(56))
print(get_height(64))
