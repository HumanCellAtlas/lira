#!/usr/bin/env python

import argparse
import requests
import re

class Tag:
    def __init__(self, major, minor, patch):
        self.v = [major, minor, patch]
        self.string = '{0}.{1}.{2}'.format(self.v[0], self.v[1], self.v[2])

    def __str__(self):
        return self.string

    def __eq__(self, other):
        return self.string == other.string

    def __gt__(self, other):
        for s, o in zip(self.v, other.v):
            if s < o:
                return False
            if s > o:
                return True
        return False

def run(repo):
    url = 'https://api.github.com/repos/{0}/git/refs/tags/'.format(repo) 
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError('Return code was {0} for {1}, message:\n'.format(response.status_code, url, response.json()))
    
    p = re.compile(r'^(\d+)\.(\d+)\.(\d+)$')
    tags = []
    max_tag = Tag(0, 0, 0)
    for tag_object in response.json():
        tag_str = tag_object['ref'][10:]
        m = p.match(tag_str)
        if m:
            tag = Tag(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            if tag > max_tag:
                max_tag = tag
    print(max_tag)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo')
    args = parser.parse_args()
    run(args.repo)
