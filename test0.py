for i in range(3):
    for j in range(3):
        print(i, j)
        if i == 1:
            break
    else:
        continue
    break

a = [1, 2, 3, 4, 5]
a.remove(2)
print(a)
