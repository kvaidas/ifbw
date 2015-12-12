import argparse
import time
import signal

#
# Parameter parsing
#
argparser = argparse.ArgumentParser()
argparser.add_argument(
    '-n',
    metavar='<iterations>',
    dest='iterations',
    default=-1,
    help='how many iterations to perform before exiting (defaults to infinite)'
)
argparser.add_argument(
    '-i',
    '--interval',
    metavar='<seconds>',
    default=1,
    help='interval between measurements'
)
argparser.add_argument(
    metavar='interface',
    dest='interface_list',
    nargs='*',
    default='all',
    help='list of interfaces, separated by spaces, defaults to all interfaces'
)
argparser.add_argument(
    '-d',
    action='store_const',
    const='True',
    dest='debug',
    help='turn on debug mode (developers only)'
)
arguments = argparser.parse_args()
if arguments.debug: print(arguments)

#
# Function for gathering data from system counters
#
def gather_interface_data():
    datafile = open("/proc/net/dev","r")
    # Skip the headers
    datafile.readline()
    datafile.readline()

    interfaces = {}
    for line in datafile:
        interface_info = line.replace(':', ' ').split()
        interface = interface_info[0]
        # check if reading info about an interface we're interested in
        if \
            interface not in arguments.interface_list and \
            'all' != arguments.interface_list             \
        :
            continue
        interfaces[interface] = {}
        interfaces[interface]['bytes_received']   = int(interface_info[ 1])
        interfaces[interface]['packets_received'] = int(interface_info[ 2])
        interfaces[interface]['bytes_sent']       = int(interface_info[ 9])
        interfaces[interface]['packets_sent']     = int(interface_info[10])

    datafile.close()
    return interfaces

#
# Function for making larger numbers (of data) more human-readable
#
def data_human(data):
    data = float(data)
    order = 0 # of magnitude - index for the array below
    units = ['B', 'kB', 'MB', 'GB']
    while True:
        if data > 1024:
            data /= 1024
            order += 1
        else:
            break

    return  { 'amount':data, 'units':units[order] }

#
# Function that calculates the rates and prints them
#
def print_rates():
    counters_before = gather_interface_data()
    time.sleep( float(arguments.interval) )
    counters_after = gather_interface_data()

    # loop through interfaces that data has been collected about
    for interface in counters_before:
        # Calculate differences
        bytes_received   = counters_after[interface]['bytes_received']   - \
                          counters_before[interface]['bytes_received']
        packets_received = counters_after[interface]['packets_received'] - \
                          counters_before[interface]['packets_received']
        bytes_sent       = counters_after[interface]['bytes_sent']       - \
                          counters_before[interface]['bytes_sent']
        packets_sent     = counters_after[interface]['packets_sent']     - \
                          counters_before[interface]['packets_sent']
        # Data rates per second
        bytes_received_rate   = int( bytes_received   / float(arguments.interval) )
        packets_received_rate = int( packets_received / float(arguments.interval) )
        bytes_sent_rate       = int( bytes_sent       / float(arguments.interval) )
        packets_sent_rate     = int( packets_sent     / float(arguments.interval) )
        # Print the result
        print(
            '{0:>4s}: Download: {1:>5.1f} {2:<4s}, Upload: {3:>5.1f} {4:s}'.format(
                interface,
                data_human(bytes_received_rate)['amount'],
                data_human(bytes_received_rate)['units'] + '/s',
                data_human(bytes_sent_rate)['amount'],
                data_human(bytes_sent_rate)['units'] + '/s'
             )
        )

#
# ctrl+c handler
#
def sigint_handler(signum, frame):
    print
    exit(0)

#
# Main loop
#
signal.signal(signal.SIGINT, sigint_handler)

if (-1) == arguments.iterations:
    while True:
        print_rates()
else:
    for iteration in range(0, int(arguments.iterations)):
        print_rates()
