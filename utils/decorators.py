def get_len():
    def wrapper(*args,**kwargs):
        result = wrapper(*args,**kwargs)
        if result:
            return len(result)
        else:
            return 0
    return wrapper