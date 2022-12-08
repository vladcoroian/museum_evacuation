from argparse import ArgumentParser
import pprint
from argparse import ArgumentParser
from numpy.random import PCG64, Generator

# local project imports
from simulator import Simulator

pp = pprint.PrettyPrinter(indent=4).pprint


def main():
    parser = ArgumentParser()
    parser.add_argument('-i', '--input', type=str,
                        default='in/museum.txt',
                        help='input floor plan file (default: '
                             'in/twoexitbottleneck.py)')
    parser.add_argument('-n', '--numpeople', type=int, default=10,
                        help='number of people in the simulation (default:10)')
    parser.add_argument('-r', '--random_state', type=int, default=8675309,
                        help='aka. seed (default:8675309)')
    parser.add_argument('-t', '--max_time', type=float, default=None,
                        help='the building collapses at this clock tick. people'
                             ' beginning movement before this will be assumed'
                             ' to have moved away sufficiently (safe)')
    parser.add_argument('-g', '--no_graphical_output', action='store_true',
                        help='disallow graphics?')
    parser.add_argument('-o', '--output', action='store_true',
                        help='show excessive output?')
    parser.add_argument('-b', '--bottleneck_delay', type=float, default=1,
                        help='how long until the next person may leave the B')
    parser.add_argument('-a', '--animation_delay', type=float, default=1,
                        help='delay per frame of animated visualization (s)')
    args = parser.parse_args()
    # output them as a make-sure-this-is-what-you-meant
    print('commandline arguments:', args, '\n')

    # set up random streams
    streams = [Generator(PCG64(args.random_state)) for i in range(5)]
    loc_strm, strat_strm, rate_strm, pax_strm, fire_strm = streams

    location_sampler = loc_strm.choice  # used to make initial placement of pax
    def strategy_generator(): return strat_strm.uniform(.5, 1)  # used to pick move

    def rate_generator(): return max(.1, abs(rate_strm.normal(1, .1)))  # used to
    # decide
    # strategies

    def person_mover(): return pax_strm.uniform()

    # create an instance of Floor
    floor = Simulator(args.input, args.numpeople, location_sampler,
                    strategy_generator, rate_generator, person_mover,
                    bottleneck_delay=args.bottleneck_delay,
                    animation_delay=args.animation_delay, verbose=args.output)

    # call the simulate method to run the actual simulation

    floor.simulate(maxtime=args.max_time, gui=not args.no_graphical_output)
    floor.stats()


if __name__ == '__main__':
    main()
