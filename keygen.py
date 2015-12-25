import string
import random


def get_random_string(min_, max_):
    source_string = string.ascii_letters + string.digits + string.punctuation
    str_len = random.randrange(min_, max_)
    return ''.join(random.choice(source_string) for _ in range(str_len))

print(get_random_string(32, 64))