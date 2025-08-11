import sys, getopt, os
from pathlib import Path

all_vlans = []

def print_usage():
    print('LCDN Client Module:')
    print()
    print('Options:')
    print('\t-s, --unix-socket <socket_name>: Opens a Unix Socket with under /tmp/lcdn/<socket_name>. It is intended to use when not using the python-native API for LCDN Clients.')
    print('\t-i, --interface: <interface> specifies the interface that should be used for LCDN Traffic.')
print_usage
def check_sudo() -> bool:
    return os.getuid() == 0

def create_vlan():
    return

def check_interface(interface_name: str) -> bool:
    if Path(f'/sys/class/net/{interface_name}').exists():
        return True

    return False

def main(argv):
    inteface = ''
    socket = ''

    try:
        opts, args = getopt.getopt(argv, "hi:s:", ["help", "interface=", "unix-socket="])
    except getopt.GetoptError:
        print_usage()
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-h':
            print_usage()
            sys.exit()
        elif opt in ("-i", "--interface"):
            inteface = arg
        elif opt in ("-s", "--unix-socket"):
            socket = arg

    is_sudo = check_sudo()

    if not is_sudo:
        print('This must be run as root.')
        sys.exit()

    interface_exists = check_interface(inteface)

    if not interface_exists:
        print(f'The interface {inteface} does not exist.')




if __name__ == '__main__':
    main(sys.argv[1:])
