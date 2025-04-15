"""Comprehensive key mapping for evemu events.

Contains mappings from human-readable keys to evemu key codes.
Based on Linux input event codes from:
https://www.kernel.org/doc/html/latest/input/event-codes.html
https://github.com/torvalds/linux/blob/master/include/uapi/linux/input-event-codes.h
"""

# Main alphanumeric keys (verified)
ALPHA_KEYS = {
    'a': 'KEY_A', 'b': 'KEY_B', 'c': 'KEY_C', 'd': 'KEY_D', 'e': 'KEY_E',
    'f': 'KEY_F', 'g': 'KEY_G', 'h': 'KEY_H', 'i': 'KEY_I', 'j': 'KEY_J',
    'k': 'KEY_K', 'l': 'KEY_L', 'm': 'KEY_M', 'n': 'KEY_N', 'o': 'KEY_O',
    'p': 'KEY_P', 'q': 'KEY_Q', 'r': 'KEY_R', 's': 'KEY_S', 't': 'KEY_T',
    'u': 'KEY_U', 'v': 'KEY_V', 'w': 'KEY_W', 'x': 'KEY_X', 'y': 'KEY_Y',
    'z': 'KEY_Z',
    '0': 'KEY_0', '1': 'KEY_1', '2': 'KEY_2', '3': 'KEY_3', '4': 'KEY_4',
    '5': 'KEY_5', '6': 'KEY_6', '7': 'KEY_7', '8': 'KEY_8', '9': 'KEY_9',
}

# Modifier and special keys (verified)
MODIFIER_KEYS = {
    'shift': 'KEY_LEFTSHIFT',
    'ctrl': 'KEY_LEFTCTRL',
    'alt': 'KEY_LEFTALT',
    'meta': 'KEY_LEFTMETA',
    'super': 'KEY_LEFTMETA',
    'space': 'KEY_SPACE',
    'enter': 'KEY_ENTER',
    'tab': 'KEY_TAB',
    'backspace': 'KEY_BACKSPACE',
    'esc': 'KEY_ESC',
    'delete': 'KEY_DELETE',
    'insert': 'KEY_INSERT',
    'capslock': 'KEY_CAPSLOCK',
}

# Function keys (verified)
FUNCTION_KEYS = {
    'f1': 'KEY_F1', 'f2': 'KEY_F2', 'f3': 'KEY_F3', 'f4': 'KEY_F4',
    'f5': 'KEY_F5', 'f6': 'KEY_F6', 'f7': 'KEY_F7', 'f8': 'KEY_F8',
    'f9': 'KEY_F9', 'f10': 'KEY_F10', 'f11': 'KEY_F11', 'f12': 'KEY_F12',
    'f13': 'KEY_F13', 'f14': 'KEY_F14', 'f15': 'KEY_F15', 'f16': 'KEY_F16',
    'f17': 'KEY_F17', 'f18': 'KEY_F18', 'f19': 'KEY_F19', 'f20': 'KEY_F20',
    'f21': 'KEY_F21', 'f22': 'KEY_F22', 'f23': 'KEY_F23', 'f24': 'KEY_F24',
}

# Arrow and navigation keys (verified)
NAVIGATION_KEYS = {
    'up': 'KEY_UP',
    'down': 'KEY_DOWN',
    'left': 'KEY_LEFT',
    'right': 'KEY_RIGHT',
    'home': 'KEY_HOME',
    'end': 'KEY_END',
    'pageup': 'KEY_PAGEUP',
    'pagedown': 'KEY_PAGEDOWN',
}

# Numpad keys (verified)
NUMPAD_KEYS = {
    'num0': 'KEY_KP0', 'num1': 'KEY_KP1', 'num2': 'KEY_KP2', 'num3': 'KEY_KP3',
    'num4': 'KEY_KP4', 'num5': 'KEY_KP5', 'num6': 'KEY_KP6', 'num7': 'KEY_KP7',
    'num8': 'KEY_KP8', 'num9': 'KEY_KP9',
    'numlock': 'KEY_NUMLOCK',
    'numdivide': 'KEY_KPSLASH',
    'nummultiply': 'KEY_KPASTERISK',
    'numminus': 'KEY_KPMINUS',
    'numplus': 'KEY_KPPLUS',
    'numenter': 'KEY_KPENTER',
    'numdot': 'KEY_KPDOT',
}

# Combine all key mappings
KEY_MAP = {
    **ALPHA_KEYS,
    **MODIFIER_KEYS,
    **FUNCTION_KEYS,
    **NAVIGATION_KEYS,
    **NUMPAD_KEYS,
    # Additional special characters (verified)
    '`': 'KEY_GRAVE',
    '-': 'KEY_MINUS',
    '=': 'KEY_EQUAL',
    '[': 'KEY_LEFTBRACE',
    ']': 'KEY_RIGHTBRACE',
    '\\': 'KEY_BACKSLASH',
    ';': 'KEY_SEMICOLON',
    "'": 'KEY_APOSTROPHE',
    ',': 'KEY_COMMA',
    '.': 'KEY_DOT',
    '/': 'KEY_SLASH',
}
