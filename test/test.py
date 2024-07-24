data1 = {
    "name1": "1111",
    "name2": "2222"
}
data2 = {
    "name3": "2222",
    "name4": "33333"
}
data3 = {
    "name5": "3333",
    "name6": "4444"
}

def extend(*dictionary):
    for d in dictionary:
        for key in d.keys():
            print(key)

extend(data1, data2, data3)