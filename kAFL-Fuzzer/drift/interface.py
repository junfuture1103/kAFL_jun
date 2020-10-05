class Interface:
    """A set of interfaces is the result of interface recovery phase.
    Each interface denotes a control code associated with constraints."""
    next_id = 1

    def __init__(self, code):
        self.id = Interface.next_id # interface id
        self.code = code            # IOCTL code
        Interface.next_id += 1