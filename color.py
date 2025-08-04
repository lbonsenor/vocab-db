class colors:
   PURPLE = '\033[95m'
   CYAN = '\033[96m'
   DARKCYAN = '\033[36m'
   BLUE = '\033[94m'
   GREEN = '\033[92m'
   YELLOW = '\033[93m'
   RED = '\033[91m'
   BOLD = '\033[1m'
   UNDERLINE = '\033[4m'
   END = '\033[0m'

def purple(str):
   return colors.PURPLE + str + colors.END

def cyan(text):
   return colors.CYAN + text + colors.END

def darkcyan(text):
   return colors.DARKCYAN + text + colors.END

def blue(text):
   return colors.BLUE + text + colors.END

def green(text):
   return colors.GREEN + text + colors.END

def yellow(text):
   return colors.YELLOW + text + colors.END

def red(text):
   return colors.RED + text + colors.END

def bold(text):
   return colors.BOLD + text + colors.END

def underline(text):
   return colors.UNDERLINE + text + colors.END