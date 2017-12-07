#!/usr/bin/env python
# coding: utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
try:
    import configparser
except ImportError:
    import ConfigParser as configparser
import io
import operator
import os
import sys

import requests

PATH = 'https://cloud.centos.org/centos/7/images/'
INDEX = PATH + 'image-index'

LATEST = 'latest'


def image_index():
    index = requests.get(INDEX)
    filelike = io.StringIO(index.text)
    cp = configparser.ConfigParser()
    cp.readfp(filelike)
    data = {sec: dict(cp.items(sec)) for sec in cp.sections()}
    for sec in data:
        data[sec]['url'] = PATH + data[sec]['file']
    return data


def newest_image():
    return max(image_index().values(), key=operator.itemgetter('revision'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('-r', '--revision', type=str, default=LATEST,
        help='Revision to build with, usually of the format YYMM')
    parser.add_argument('variant', type=str,
        help='Image variant to build.') # extra elements defined in the .sh

    args = parser.parse_args()

    if args.revision == LATEST:
        image = newest_image()
    else:
        try:
            image = next(i for i in image_index().values() if i['revision'] == args.revision)
        except StopIteration:
            print("No image found for revision '{}'".format(args.revision))
            return 1

    # os.environ['IMAGE_URL'] = image['url']
    os.environ['BASE_IMAGE_XZ'] = image['file']
    os.environ['IMAGE_REVISION'] = image['revision']
    os.environ['IMAGE_SHA512'] = image['checksum']
    os.environ['BASE_IMAGE'] = image['file'][:-3]

    os.execl('create-image.sh', 'create-image.sh', args.variant)

if __name__ == '__main__':
    sys.exit(main())
