"""
    sqmpy
    ~~~~~

    This file is part of sqmpy project.
"""
import zerorpc

from sqmpy import app

__author__ = 'Mehdi Sadeghi'


def list_peers():
    """
    Return available network peers
    :return:
    """
    peers = {'peer1': {'id': '#1', 'address': 'pc-p282', 'status': 'Ready'}}
    c = zerorpc.Client()
    c.connect(app.config.get('CONSENSUS_SERVER'))
    p = c.get_peers()
    if p:
        peers.update(p)
    return peers