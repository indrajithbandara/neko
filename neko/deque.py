"""
Simplifies the list data-structure interface to behave as a stack, queue, or
deque.
"""


class ReadOnlyIterable:
    """Provides readonly access to a list."""
    __slots__ = ('_list',)

    def __init__(self, *items):
        self._list = [*items]

    def __contains__(self, item):
        return item in self._list

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def __str__(self):
        return str(self._list)

    def __repr__(self):
        return repr(self._list)

    def __reversed__(self):
        return self._list.reverse()


class Stack(ReadOnlyIterable):
    """Provides FILO access to a read-only iterable."""
    def push(self, *items):
        """Pushes items in order to the end."""
        [self._list.append(item) for item in items]

    def pop(self, n: int=1):
        """
        Pop from the end of the collection.
        :param n: defaults to 1. Number of elements to pop.
        :return: the element, or elements in a tuple if n > 1.
        """
        assert n > 0
        if n == 1:
            return self._list.pop()
        else:
            return tuple(self.pop() for _ in range(0, n))


class Queue(ReadOnlyIterable):
    """Provides FIFO access tp a read-only iterable."""
    def unshift(self, *items):
        """
        Unshifts items in reverse order to the start.

        e.g. unshift(1, 2, 3) will produce [3, 2, 1] internally.
        """
        [self._list.insert(0, item) for item in items]

    def shift(self, n: int=1):
        """
        Shifts from the start of the collection.
        :param n: defaults to 1. Number of elements to shift.
        :return: the element, or elements in a tuple if n > 1
        """
        assert n > 0
        if n == 1:
            return self._list.pop(0)
        else:
            return tuple(self.shift() for _ in range(0, n))


class Deque(Stack, Queue):
    """Provides LIFO and FIFO access to a read-only iterable."""
    pass

