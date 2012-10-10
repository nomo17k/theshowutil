#!/usr/bin/env python2.7
"""Lahman database driver module

This module provides a singleton interface to the Lahman database.
The instantiation of database connection is done lazily to prevent
openning a connection to be never used, since the web-based
application has its own flow of using the database and would not use
this module.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
#from __future__ import unicode_literals
import os
import MySQLdb
import numpy as np


DATABASE = 'lahman591'
DEFAULT_FILE = '/'.join([os.environ.get('HOME', '~'), ".my.cnf"])


_db = None


def connect():
    global _db
    if _db:
        return _db
    _db = MySQLdb.connect(db=DATABASE,
                          read_default_file=DEFAULT_FILE)
    return _db


def cursor(cursorclass=None):
    global _db
    _db = _db if _db else connect()
    if cursorclass:
        return _db.cursor(cursorclass)
    return _db.cursor()


class LahmanReader(object):
    """Lahman database conversion utility"""

    dtype = []

    @classmethod
    def fromiter(cls, iter):
        d = np.array([], dtype=cls.dtype)
        mask = []
        for size, o in enumerate(iter):
            d.resize(size + 1)
            ms = np.zeros((len(o),), dtype=bool)
            for i, x in enumerate(o):
                dt = cls.dtype[i][1][0]
                ms[i] = (x is None)
                x = (x if x is not None
                     else (-99999 if dt == 'i'
                           else (-99999. if dt == 'f'
                                 else '')))
                d[-1][i] = x
            mask.append(tuple(ms))
        d = np.ma.array(d, mask=mask)
        return d


class Master(LahmanReader):

    dtype = [('lahmanID', 'i'),
             ('playerID', 'a9'),
             ('managerID', 'a10'),
             ('hofID', 'a10'),
             ('birthYear', 'i'),
             ('birthMonth', 'i'),
             ('birthDay', 'i'),
             ('birthCountry', 'a24'),
             ('birthState', 'a2'),
             ('birthCity', 'a31'),
             ('deathYear', 'i'),
             ('deathMonth', 'i'),
             ('deathDay', 'i'),
             ('deathCountry', 'a34'),
             ('deathState', 'a2'),
             ('deathCity', 'a21'),
             ('nameFirst', 'a12'),
             ('nameLast', 'a14'),
             ('nameNote', 'a80'),
             ('nameGiven', 'a43'),
             ('nameNick', 'a48'),
             ('weight', 'f'),
             ('height', 'f'),
             ('bats', 'a1'),
             ('throws', 'a1'),
             ('debut', 'a18'),
             ('finalGame', 'a18'),
             ('college', 'a40'),
             ('lahman40ID', 'a9'),
             ('lahman45ID', 'a9'),
             ('retroID', 'a8'),
             ('holtzID', 'a9'),
             ('bbrefID', 'a9')]


class Batting(LahmanReader):
    
    dtype = [("playerID", 'a9'),
             ("yearID", 'i'),
             ("stint", 'i'),
             ("teamID", 'a3'),
             ("lgID", 'a2'),
             ("G", 'i'),
             ("G_batting", 'i'),
             ("AB", 'i'),
             ("R", 'i'),
             ("H", 'i'),
             ("2B", 'i'),
             ("3B", 'i'),
             ("HR", 'i'),
             ("RBI", 'i'),
             ("SB", 'i'),
             ("CS", 'i'),
             ("BB", 'i'),
             ("SO", 'i'),
             ("IBB", 'i'),
             ("HBP", 'i'),
             ("SH", 'i'),
             ("SF", 'i'),
             ("GIDP", 'i'),
             ("G_old", 'i')]


class Pitching(LahmanReader):

    dtype = [("playerID", 'a9'),
             ("yearID", 'i'),
             ("stint", 'i'),
             ("teamID", 'a3'),
             ("lgID", 'a2'),
             ("W", 'i'),
             ("L", 'i'),
             ("G", 'i'),
             ("GS", 'i'),
             ("CG", 'i'),
             ("SHO", 'i'),
             ("SV", 'i'),
             ("IPouts", 'i'),
             ("H", 'i'),
             ("ER", 'i'),
             ("HR", 'i'),
             ("BB", 'i'),
             ("SO", 'i'),
             ("BAOpp", 'f'),
             ("ERA", 'f'),
             ("IBB", 'i'),
             ("WP", 'i'),
             ("HBP", 'i'),
             ("BK", 'i'),
             ("BFP", 'i'),
             ("GF", 'i'),
             ("R", 'i'),
             ("SH", 'i'),
             ("SF", 'i'),
             ("GIDP", 'i')]


class Fielding(LahmanReader):

    dtype = [("playerID", 'a9'),
             ("yearID", 'i'),
             ("stint", 'i'),
             ("teamID", 'a3'),
             ("lgID", 'a2'),
             ("POS", 'a2'),
             ("G", 'i'),
             ("GS", 'i'),
             ("InnOuts", 'i'),
             ("PO", 'i'),
             ("A", 'i'),
             ("E", 'i'),
             ("DP", 'i'),
             ("PB", 'i'),
             ("WP", 'i'),
             ("SB", 'i'),
             ("CS", 'i'),
             ("ZR", 'f')]


class Appearances(LahmanReader):

    dtype = [("yearID", 'i'),
             ("teamID", 'a3'),
             ("lgID", 'a2'),
             ("playerID", 'a9'),
             #("UNKNOWN", 'i'),
             ("G_all", 'i'),
             ("GS", 'i'),
             ("G_batting", 'i'),
             ("G_defense", 'i'),
             ("G_p", 'i'),
             ("G_c", 'i'),
             ("G_1b", 'i'),
             ("G_2b", 'i'),
             ("G_3b", 'i'),
             ("G_ss", 'i'),
             ("G_lf", 'i'),
             ("G_cf", 'i'),
             ("G_rf", 'i'),
             ("G_of", 'i'),
             ("G_dh", 'i'),
             ("G_ph", 'i'),
             ("G_pr", 'i')]
