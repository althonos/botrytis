# coding: utf-8


def sentence(message):
    message = message.strip().rstrip('.')
    return "".join([message[0].upper(), message[1:], '.'])

def quote(message):
    return f"{message!r}"
