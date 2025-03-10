import random

FILE_SIZE = 4096

random_string = ''.join(chr(random.randint(32, 126)) for _ in range(FILE_SIZE))

with open("input.txt", "w") as file:
    file.write(random_string)

print(f"{FILE_SIZE}-byte random string to ./input.txt")