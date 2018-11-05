import sys
import time
import argparse

def fizzbuzz(start: int = 1, max: int = 100, out_mult: int = 3, err_mult: int = 5, pause: float = 1) -> None:
    for n in range(start, max+1):
        if n % out_mult == 0:
            print(f'{n}', file=sys.stdout)
            sys.stdout.flush()
        if n % err_mult == 0:
            print(f'{n}', file=sys.stderr)
            sys.stderr.flush()
        time.sleep(pause)

def setup_parser()-> argparse.ArgumentParser:
    parser = argparse.ArgumentParser("script to use to test command exicution code")
    parser.add_argument('stdin', nargs='?', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('-E', '--echo', action='store_true', help='echos stdin to stdout')
    parser.add_argument('-F', '--fizzbuzz', action='store_true', help='do a variation of the fizzbuzz problem but with stdout and stderr')
    parser.add_argument('-I', '--inputoutput', action='store_true', help='take input and return it as output')
    parser.add_argument('-s', '--start', type=int, default=1, help='the number to start from')
    parser.add_argument('-S', '--stop', type=int, default=100, help='the number to stop at')
    parser.add_argument('-o', '--stdoutmult', type=int, default=3, help='all numbers that are a multiple of this will be printed on stdout')
    parser.add_argument('-e', '--stderrmult', type=int, default=5, help='all numbers that are a multiple of this will be printed on stderr')
    parser.add_argument('-p', '--pause', type=float, default=0.1, help='the duration of pause in seconds between each number')

    return parser


if __name__ == '__main__':
    parser = setup_parser()
    args = parser.parse_args()

    if args.echo:
        print("".join(args.stdin.readlines()), end='')

    if args.fizzbuzz:
        fizzbuzz(args.start, args.stop, args.stdoutmult, args.stderrmult, args.pause)

    if args.inputoutput:
        response = input('your input: ')
        print(f'your response: {response}')
