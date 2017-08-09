"""
Read and write DyNetx graphs as edge lists.

The multi-line adjacency list format is useful for graphs with nodes
that can be meaningfully represented as strings.

With the edgelist format simple edge data can be stored but node or graph data is not.
There is no way of representing isolated nodes unless the node has a self-loop edge.

Format
------
You can read or write three formats of edge lists with these functions.

Node pairs with **timestamp** (u, v, t):

>>> 1 2 0

Sequence of **Interaction** events (u, v, +/-, t):

>>> 1 2 + 0
>>> 1 2 - 3
"""

from dynetx.utils import open_file, make_str, clean_timeslot
from dynetx import DynGraph

__author__ = 'Giulio Rossetti'
__license__ = "GPL"
__email__ = "giulio.rossetti@gmail.com"

__all__ = ['write_interactions',
           'generate_interactions',
           'parse_interactions',
           'read_interactions',
           'generate_snapshots',
           'write_snapshots',
           'parse_snapshots',
           'read_snapshots']


def generate_interactions(G, delimiter=' '):
    for e in G.stream_interactions():
        yield delimiter.join(map(make_str, e))


@open_file(1, mode='wb')
def write_interactions(G, path, delimiter=' ',  encoding='utf-8'):
    """Write a DyNetx graph in interaction list format.


        Parameters
        ----------

        G : graph
            A DyNetx graph.

        path : basestring
            The desired output filename

        delimiter : character
            Column delimiter
        """
    for line in generate_interactions(G, delimiter):
        line += '\n'
        path.write(line.encode(encoding))


@open_file(0, mode='rb')
def read_interactions(path, comments="#", delimiter=None, create_using=None,
                  nodetype=None, timestamptype=None, encoding='utf-8', keys=False):
    """Read a DyNetx graph from interaction list format.


        Parameters
        ----------

        path : basestring
            The desired output filename

        delimiter : character
            Column delimiter
    """
    ids = None
    lines = (line.decode(encoding) for line in path)
    if keys:
        ids = read_ids(path.name, delimiter=delimiter, timestamptype=timestamptype)

    return parse_interactions(lines, comments=comments, delimiter=delimiter, create_using=create_using, nodetype=nodetype,
                             timestamptype=timestamptype, keys=ids)


def parse_interactions(lines, comments='#', delimiter=None, create_using=None, nodetype=None, timestamptype=None, keys=None):
    if create_using is None:
        G = DynGraph()
    else:
        try:
            G = create_using
            G.clear()
        except:
            raise TypeError("create_using input is not a DyNet graph type")

    for line in lines:

        p = line.find(comments)
        if p >= 0:
            line = line[:p]
        if not len(line):
            continue

        s = line.strip().split(delimiter)

        if len(s) != 4:
            continue
        else:
            u = s.pop(0)
            v = s.pop(0)
            op = s.pop(0)
            s = s.pop(0)

        if nodetype is not None:
            try:
                u = nodetype(u)
                v = nodetype(v)
            except:
                raise TypeError("Failed to convert nodes %s,%s to type %s." % (u, v, nodetype))

        if timestamptype is not None:
            try:
                s = timestamptype(s)
            except:
                raise TypeError("Failed to convert timestamp %s to type %s." % (s, nodetype))
        if op == '+':
            if keys is not None:
                G.add_interaction(u, v, t=keys[s])
            else:
                G.add_interaction(u, v, t=s)
        else:
            timestamps = G.edge[u][v]['t']
            if len(timestamps) > 0 and timestamps[-1] < s:
                for t in range(timestamps[-1], s):
                    if keys is not None:
                        G.add_interaction(u, v, t=keys[t])
                    else:
                        G.add_interaction(u, v, t=t)
    return G


def generate_snapshots(G, delimiter=' '):

    for u, v, d in G.interactions():
        if 't' not in d:
            raise NotImplemented
        for t in d['t']:
            e = [u, v, t[0]]
            if t[1] is not None or t[0] != t[1]:
                for s in xrange(t[0], t[1]):
                    e = [u, v, t]

            try:
                e.extend(d[k] for k in d if k != "t")
            except KeyError:
                pass
            yield delimiter.join(map(make_str, e))


@open_file(1, mode='wb')
def write_snapshots(G, path, delimiter=' ', encoding='utf-8'):
    """Write a DyNetx graph in snapshot graph list format.


        Parameters
        ----------

        G : graph
            A DyNetx graph.

        path : basestring
            The desired output filename

        delimiter : character
            Column delimiter
        """
    for line in generate_snapshots(G, delimiter):
        line += '\n'
        path.write(line.encode(encoding))


def parse_snapshots(lines, comments='#', delimiter=None, create_using=None, nodetype=None, timestamptype=None, keys=None):

    if create_using is None:
        G = DynGraph()
    else:
        try:
            G = create_using
            G.clear()
        except:
            raise TypeError("create_using input is not a DyNet graph type")

    for line in lines:
        p = line.find(comments)
        if p >= 0:
            line = line[:p]
        if not len(line):
            continue
        # split line, should have 2 or more
        s = line.strip().split(delimiter)
        if len(s) < 3:
            continue
        if len(s) == 3:
            u = s.pop(0)
            v = s.pop(0)
            t = s.pop(0)
            e = None
        else:
            u = s.pop(0)
            v = s.pop(0)
            t = s.pop(0)
            e = s.pop(0)

        if nodetype is not None:
            try:
                u = nodetype(u)
                v = nodetype(v)
            except:
                raise TypeError("Failed to convert nodes %s,%s to type %s." % (u, v, nodetype))

        if timestamptype is not None:
            try:
                t = timestamptype(t)
            except:
                raise TypeError("Failed to convert timestamp %s to type %s." % (t, nodetype))
        if keys is not None:
            if e is not None:
                G.add_interaction(u, v, t=keys[t], e=keys[e])
            else:
                G.add_interaction(u, v, t=keys[t], e=e)
        else:
            G.add_interaction(u, v, t=t, e=e)
    return G


@open_file(0, mode='rb')
def read_snapshots(path, comments="#", delimiter=None, create_using=None,
                   nodetype=None, timestamptype=None, encoding='utf-8', keys=False):
    """Read a DyNetx graph from snapshot graph list format.


        Parameters
        ----------

        path : basestring
            The desired output filename

        delimiter : character
            Column delimiter
    """
    ids = None
    lines = (line.decode(encoding) for line in path)
    if keys:
        ids = read_ids(path.name, delimiter=delimiter, timestamptype=timestamptype)

    return parse_snapshots(lines, comments=comments, delimiter=delimiter, create_using=create_using, nodetype=nodetype,
                           timestamptype=timestamptype, keys=ids)


def read_ids(path, delimiter=None, timestamptype=None):
    f = open(path)
    ids = {}
    for line in f:
        s = line.rstrip().split(delimiter)
        ids[timestamptype(s[-1])] = None
        if len(line) == 4:
            if s[-2] not in ['+', '-']:
                ids[timestamptype(s[-2])] = None

    f.flush()
    f.close()

    ids = clean_timeslot(ids.keys())
    return ids
