#  This file is part of easygdf and is released under the BSD 3-clause license

import numpy as np
import argparse
from pathlib import Path

from .easygdf import save


def main(args=None):
    # Configure parser
    parser = argparse.ArgumentParser(description='Convert tab-delimited files to GDF')
    parser.add_argument('-o', metavar='outfile', type=str, help='write output to the file', action='store')
    parser.add_argument(metavar='infile', dest='infile', type=str, help='file to convert', action='store')
    parser.add_argument('--scale', metavar=('name', 'factor'), nargs=2, dest='scale', type=str,
                        help='optionally scale specified array', action='append')
    args = parser.parse_args(args)

    # Load the input data
    rdat = np.genfromtxt(args.infile, skip_header=1)
    with open(args.infile) as f:
        header = f.readline().strip().split('\t')
    if len(header) != rdat.shape[1]:
        raise ValueError(f'Number of header columns must match number of data columns, '
                         f'got {len(header)} and {rdat.shape[1]} instead')

    # Scale the data
    dat = {k: v for k, v in zip(header, rdat.T)}
    if args.scale is not None:
        for name, fac in args.scale:
            dat[name] = float(fac) * dat[name]

    # Save the data
    outfile = Path(args.infile).with_suffix('.gdf') if args.o is None else args.o
    save(str(outfile), blocks=[{'name': n, 'value': v} for n, v in dat.items()])


if __name__ == '__main__':
    main()
