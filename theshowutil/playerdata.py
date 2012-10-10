#!/usr/bin/env python2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
#from __future__ import unicode_literals
from . import lahmandb
from MySQLdb.cursors import DictCursor, Cursor
import numpy as np
from theshowutil.ratinggenerator import BasicRatingGenerator


def outs2inn(outs):
    outs = int(round(outs))
    return ('{}.{}'.format(outs // 3, outs % 3) if outs % 3 > 0
            else '{}  '.format(outs // 3))


def in2ft(inch):
    inch = int(round(inch))
    return '{:1d}-{:d}'.format(inch // 12, inch % 12)


class NoPlayerFoundError(Exception): pass
class NoPlayingTimeError(Exception): pass


class PlayerData(object):

    def __init__(self, playerid, currentyear, yweight={}, db=lahmandb):
        self.playerid = playerid
        self.currentyear = int(currentyear)

        if yweight is None or len(yweight) == 0:
            y = self.currentyear
            yweight = {y: 2., (y-1): 1., (y-2): 1.}
        wtot = sum([float(yw) for yw in yweight.values()])
        for y in yweight:
            yweight[y] = (yweight[y] / wtot) * len(yweight)
        self.yweight = yweight

        self._db = db
        self._init()

    def _init(self):
        pid = self.playerid

        c = self._db.cursor(DictCursor)

        c.execute("SELECT * FROM Master WHERE playerID = %s", (pid,))
        m = c.fetchall()
        if len(m) != 1:
            s = ("invalid playerID: {:s}".format(pid))
            raise NoPlayerFoundError(s)
        self.master = m[0]

        c = self._db.cursor()

        c.execute("SELECT * FROM Pitching WHERE playerID = %s", (pid,))
        self.pitching = lahmandb.Pitching.fromiter(c.fetchall())

        c.execute("SELECT * FROM Batting WHERE playerID = %s", (pid,))
        self.batting = lahmandb.Batting.fromiter(c.fetchall())

        c.execute("SELECT * FROM Fielding WHERE playerID = %s", (pid,))
        self.fielding = lahmandb.Fielding.fromiter(c.fetchall())

        c.execute("SELECT * FROM Appearances WHERE playerID = %s", (pid,))
        self.appearances = lahmandb.Appearances.fromiter(c.fetchall())

        attr = PlayerAttributes()
        attr.update_basic(self)
        self.attr = attr
        
        self.update_total()

    def age(self, year=None):
        """Player's age in given year (or currentyear)"""
        y, m = self.master['birthYear'], self.master['birthMonth']
        return (year if year else self.currentyear) - y - (m > 6)

    def update_total(self):
        w = self.yweight
        y = self.currentyear
        t = {}
        t['pitching'] = TotPitching.weighted(self.pitching, y, w)
        t['batting'] = TotBatting.weighted(self.batting, y, w)
        t['fielding'] = TotFielding.weighted(self.fielding, y, w)
        t['appearances'] = TotAppearances.weighted(self.appearances, y, w)
        self.total4rating = t

        c = BasicRatingGenerator(self.attr, self.total4rating)
        self.attr = c.rate()

    def generate_csv(self):
        return self.attr.generate_csv()


class PlayerAttributes(dict):

    def __init__(self, *args, **kwargs):
        super(PlayerAttributes, self).__init__(*args, **kwargs)
        self.reset()

    def reset(self):
        attr = {'FNM': '', 'LNM': '', 'HT': '', 'WT': '', 'PO1': '',
                'PO2': '', 'T': '', 'B': '', 'USB': '', 'AGE': -1,

                'STA': -1, 'PCL': -1, 'H9': -1, 'HR9': -1, 'K9': -1, 'BB9': -1,
                'P1': '', 'P1S': -1, 'P1C': -1, 'P1B': -1,
                'P2': '', 'P2S': -1, 'P2C': -1, 'P2B': -1,
                'P3': '', 'P3S': -1, 'P3C': -1, 'P3B': -1,
                'P4': '', 'P4S': -1, 'P4C': -1, 'P4B': -1,
                'P5': '', 'P5S': -1, 'P5C': -1, 'P5B': -1,

                'RCT': -1, 'LCT': -1, 'RPW': -1, 'LPW': -1, 'BNT': -1,
                'DBN': -1, 'VIS': -1, 'DIS': -1, 'CLU': -1, 'DUR': -1,
                'SPD': -1, 'AMS': -1, 'AMA': -1, 'REA': -1, 'FLD': -1,
                'BLK': -1, 'BAB': -1, 'BAG': -1}
        self.update(attr)

    def update_basic(self, playerdata, year=None):
        master = playerdata.master
        self['FNM'] = master['nameFirst']
        self['LNM'] = master['nameLast']
        self['HT'] = in2ft(master['height'])
        self['WT'] = master['weight']
        self['T'] = master['throws']
        self['B'] = {'R': 'R', 'L': 'L', 'B': 'S'}[master['bats']]
        self['USB'] = 'Y' if master['birthCountry'] == 'USA' else 'N'
        self['AGE'] = playerdata.age(year)

    @property
    def csvheader(self):
        h = ("#FULLNAME                  AGE HT    WT POS      T B US"
             "  RCT LCT RPW LPW BNT DBN VIS DIS CLU"
             "  DUR SPD AMS AMA REA FLD BLK BAB BAG"
             "  STA PCL  H9 HR9  K9 BB9"
             "  PT1 VL CT BR"
             "  PT2 VL CT BR"
             "  PT3 VL CT BR"
             "  PT4 VL CT BR"
             "  PT5 VL CT BR")
        return h

    @property
    def csv(self):
        d = self.copy()
        d['FULLNAME'] = '"{LNM:s}, {FNM:s}"'.format(**d)
        d['POS'] = d['PO1'] + (',{:s}'.format(d['PO2']) if d['PO2'] else '')
        if (d['PO1'] in ('SP', 'RP', 'CP')
            or d['PO2'] in ('SP', 'RP', 'CP')):
            fmp = ("{STA:2d}  {PCL:2d}  {H9:2d}  {HR9:2d}  {K9:2d}  {BB9:2d}"
                   " {P1:>4s} {P1S:2d} {P1C:2d} {P1B:2d}"
                   " {P2:>4s} {P2S:2d} {P2C:2d} {P2B:2d}"
                   " {P3:>4s} {P3S:2d} {P3C:2d} {P3B:2d}"
                   " {P4:>4s} {P4S:2d} {P4C:2d} {P4B:2d}"
                   " {P5:>4s} {P5S:2d} {P5C:2d} {P5B:2d}")
            sp = fmp.format(**d)
        else:
            sp = ""
        fmt = ('{FULLNAME:27s} {AGE:2d} {HT:<4s} {WT:3d} {POS:<8}'
               " {T:1s} {B:1s}  {USB:1s}"
               "   {RCT:2d}  {LCT:2d}  {RPW:2d}  {LPW:2d}  {BNT:2d}  {DBN:2d}"
               "  {VIS:2d}  {DIS:2d}  {CLU:2d}   {DUR:2d}  {SPD:2d}"
               "  {AMS:2d}  {AMA:2d}  {REA:2d}  {FLD:2d}  {BLK:2d}"
               "  {BAB:2d}  {BAG:2d}   " + sp)
        return fmt.format(**d)


def total(stats, fields):
    tot = {}
    for field in fields:
        tot[field] = sum(stats[field].filled(0.))
    return tot


def weighted_total(stats, fields, year, yweight=None, samplingmode='optimal'):
    if len(stats) == 0:
        # no stats recorded, so no total
        return {}

    if samplingmode == 'career':
        return total(stats)

    #def cmpkey(s):
    #    return s['yearID']

    # list all yearID values in order of summing.
    #ys_weighted = [s for s in stats if s['yearID'] in yweight.keys()]
    #ys = sorted([s for s in stats if s['yearID'] not in ys_weighted
    #             and y['yearID'] <= year], key=cmpkey, reverse=True)
    #ys.extend(sorted([y for y in self if y['yearID'] not in ys_weighted
    #                  and y['yearID'] > year], key=cmpkey))

    tot = {}
    for y in yweight:
        w = yweight[y]
        s = stats[stats['yearID'] == y]
        if len(s) == 0:
            continue
        for field in fields:
            tot[field] = (tot.setdefault(field, 0.)
                          + sum(s[field].filled(0.)) * w)
        tot['YR_TOT'] = tot.setdefault('YR_TOT', 0.) + w

    #if len(tot):
    #    tot['YRS'] = len(set([y for y in stats['yearID'])))

    ## if self.minimum_opportunity is not None:
    ##         aux_weight = (min(yweight.values()) / 2. if len(yweight.values())
    ##                       else 1.)
    ##         nmin, fields = self.minimum_opportunity

    ##         def test(total, fields):
    ##             return sum([total[field] for field in fields
    ##                         if field in total]) > nmin

    ##         for s in ys:
    ##             if test(tot, fields):
    ##                 break
    ##             # add more stats
    ##             for f in self.sumfields:
    ##                 tot[f] = (tot.setdefault(f, 0)
    ##                           + (s[f] * aux_weight if s[f] else 0))
    ##             tot['YWEIGHT'] = tot.setdefault('YWEIGHT', 0) + aux_weight

    return tot


class StatsTotal(object):

    minsample = (0, [])
    fields = ()

    @classmethod
    def weighted(cls, stats, currentyear, yweight):
        return weighted_total(stats, cls.fields, currentyear, yweight)

    @classmethod
    def normal(cls, stats):
        return total(stats, cls.fields)


class TotBatting(StatsTotal):

    minsample = (550, ['AB', 'BB', 'IBB', 'HBP', 'SH', 'SF'])
    fields = ('G', 'G_batting', 'AB', 'R', 'H', '2B', '3B', 'HR', 'RBI',
              'SB', 'CS', 'BB', 'SO', 'IBB', 'HBP', 'SH', 'SF', 'GIDP',
              'G_old')


class TotPitching(StatsTotal):

    minsample = (550, ['BFP'])
    fields = ('W', 'L', 'G', 'GS', 'CG', 'SHO', 'SV', 'IPouts', 'H', 'ER',
              'HR', 'BB', 'SO', 'IBB', 'WP', 'HBP', 'BK', 'BFP', 'GF', 'R',
              'SH', 'SF', 'GIDP')


class TotFielding(StatsTotal):

    minsample = (550, ['InnOuts'])
    fields = ('G', 'GS', 'InnOuts', 'PO', 'A', 'E', 'DP', 'PB', 'WP', 'SB',
              'CS')

    @classmethod
    def weighted(cls, stats, currentyear, yweight):
        m = ((stats['POS'] == 'P')
             + (stats['POS'] == 'C')
             + (stats['POS'] == '1B')
             + (stats['POS'] == '2B')
             + (stats['POS'] == '3B')
             + (stats['POS'] == 'SS')
             + (stats['POS'] == 'LF')
             + (stats['POS'] == 'CF')
             + (stats['POS'] == 'RF'))
        stats = stats[m]
        
        return weighted_total(stats, cls.fields, currentyear, yweight)


class TotAppearances(StatsTotal):

    minsample = (162, ['G_all'])
    fields = ('G_all', 'GS', 'G_batting', 'G_defense', 'G_p', 'G_c',
              'G_1b', 'G_2b', 'G_3b', 'G_ss', 'G_lf', 'G_cf', 'G_rf',
              'G_of', 'G_dh', 'G_ph', 'G_pr')


# class StatsTable(tuple):

#     # (minimum for statistical significance, [fields to sum])
#     minimum_opportunity = None

#     # fields to tally up
#     sumfields = ()

#     def __init__(self, rows):
#         super(StatsTable, self).__init__(null2zero(rows))

#     @property
#     def numseason(self):
#         return len(set([y['yearID'] for y in self]))

#     @property
#     def total(self):
#         tot = {}
#         for s in self:
#             for f in self.sumfields:
#                 tot[f] = tot.setdefault(f, 0) + (s[f] if s[f] else 0)
#         return tot

#     def total4rating(self, year, yweight=None, samplingmode='optimal'):
#         if len(self) == 0:
#             # no stats recorded, so no total
#             return {}

#         if samplingmode == 'career':
#             return self.total

#         def cmpkey(s):
#             return s['yearID']

#         # list all yearID values in order of summing.
#         ys_weighted = [y for y in self if y['yearID'] in yweight.keys()]
#         ys = sorted([y for y in self if y['yearID'] not in ys_weighted
#                      and y['yearID'] <= year], key=cmpkey, reverse=True)
#         ys.extend(sorted([y for y in self if y['yearID'] not in ys_weighted
#                           and y['yearID'] > year], key=cmpkey))

#         tot = {}
#         for s in ys_weighted:
#             for f in self.sumfields:
#                 yw = yweight[s['yearID']]
#                 tot[f] = (tot.setdefault(f, 0)
#                           + (s[f] * yw if s[f] else 0))
#             tot['YWEIGHT'] = tot.setdefault('YWEIGHT', 0) + yw

#         if self.minimum_opportunity is not None:
#             aux_weight = (min(yweight.values()) / 2. if len(yweight.values())
#                           else 1.)
#             nmin, fields = self.minimum_opportunity

#             def test(total, fields):
#                 return sum([total[field] for field in fields
#                             if field in total]) > nmin

#             for s in ys:
#                 if test(tot, fields):
#                     break
#                 # add more stats
#                 for f in self.sumfields:
#                     tot[f] = (tot.setdefault(f, 0)
#                               + (s[f] * aux_weight if s[f] else 0))
#                 tot['YWEIGHT'] = tot.setdefault('YWEIGHT', 0) + aux_weight

#         return tot

