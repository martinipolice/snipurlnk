import random
import string

url_store = {}

def shorten(url):
    characterPool = string.ascii_letters + string.digits
    randomCode = ''.join(random.choices(characterPool, k=6))
    
    while randomCode in url_store:
        randomCode = ''.join(random.choices(characterPool, k=6))
    
    url_store[randomCode] = url
    return randomCode


def expand(code):
    return url_store.get(code)



