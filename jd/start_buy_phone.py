import argparse
import time

from JDWrapper import JDWrapper

def main(options):
    jd = JDWrapper()
    if not jd.check_login():
        if not jd.login_by_QR():
            return

    while not jd.buy(options) and options.flush:
        time.sleep(options.wait / 1000.0)

if __name__ == '__main__':
    # help message
    parser = argparse.ArgumentParser(description='Simulate to login Jing Dong, and buy sepecified good')
    # parser.add_argument('-u', '--username',
    #                    help='Jing Dong login user name', default='')
    # parser.add_argument('-p', '--password',
    #                    help='Jing Dong login user password', default='')
    parser.add_argument('-a', '--area',
                        help='Area string, like: 1_72_2799_0 for Beijing', default='14_1116_4192_0')
    parser.add_argument('-g', '--good',
                        help='Jing Dong good ID', default='')
    parser.add_argument('-c', '--count', type=int,
                        help='The count to buy', default=1)
    parser.add_argument('-w', '--wait',
                        type=int, default=500,
                        help='Flush time interval, unit MS')
    parser.add_argument('-f', '--flush',
                        action='store_true',
                        help='Continue flash if good out of stock')
    parser.add_argument('-s', '--submit',
                        action='store_true',
                        help='Submit the order to Jing Dong')

    # example goods
    huawei_mate_20_pro = '100000822965'
    huawei_mate_20 = '100000822981'

    options = parser.parse_args()
    print options

    # for test
    if options.good == '':
        options.good = huawei_mate_20_pro
        options.flush = True
        options.submit = True

    main(options)