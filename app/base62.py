BASE62 = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"

def encode(num, alphabet):
    """Encode a positive number into Base X and return the string.

    Arguments:
    - `num`: The number to encode
    - `alphabet`: The alphabet to use for encoding
    """
    try:
        if num == 0:
            return alphabet[0]
        arr = []
        arr_append = arr.append
        _divmod = divmod
        base = len(alphabet)
        while num:
            num, rem = _divmod(num, base)
            arr_append(alphabet[rem])
        arr.reverse()
        return ''.join(arr)
    except Exception as e:
        raise e

def decode(string, alphabet=BASE62):
    """Decode a Base X encoded string into the number

    Arguments:
    - `string`: The encoded string
    - `alphabet`: The alphabet to use for decoding
    """
    try:
        base = len(alphabet)
        strlen = len(string)
        num = 0

        idx = 0
        for char in string:
            power = (strlen - (idx + 1))
            try:
                char_index = alphabet.index(char)
            except ValueError:
                raise ValueError(f"Invalid character '{char}' found in string for decoding.")
            num += char_index * (base ** power)
            idx += 1

        return num

    except Exception as e:
        raise e


# Based on an algorithm by Baishampayan Ghose on Stack Overflow
# https://stackoverflow.com/a/1119769/22179658
