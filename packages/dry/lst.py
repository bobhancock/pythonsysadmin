def flatten(alist):
    """ Flatten a list.
    If the item in the list is a list or tuple, iterate the members.
    """
    stack = [iter(alist)]

    while stack:
        current = stack.pop()

        for item in current:
            if isinstance(item, (list, tuple)):
                stack.append(current)
                stack.append(iter(item))
                break
            yield item