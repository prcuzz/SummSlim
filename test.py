import sys
import os
import re
import magic
import fnmatch


def a(input):
    if input == 1:
        return [1, 2]
    return 1


b = type(a(189342))
print(b is int)
