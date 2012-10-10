#!/usr/bin/env python2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
#from __future__ import unicode_literals
from theshowutil.playerdata import TotPitching
from theshowutil.playerdata import TotBatting
from theshowutil.playerdata import TotFielding
from theshowutil.playerdata import TotAppearances


def outs2inn(outs):
    outs = int(round(outs))
    return ('{}.{}'.format(outs // 3, outs % 3) if outs % 3 > 0
            else '{}  '.format(outs // 3))


class ViewStats(object):

    header = ''
    fmt = ''

    def __init__(self, playerdata, stats):
        self.playerdata = playerdata
        self.stats = stats

    def compute_total(self):
        return {}

    def compute_per_season(self, total):
        return {}

    def render(self):
        print(self.header)
        print('-' * len(self.header))
        stats = self.stats.filled(0.)
        for eachstats in stats:
            o = self.rendereach(eachstats)
            print(self.fmt.format(**o))

        tot = self.compute_total()
        n162 = self.compute_per_season(tot)

        print('-' * len(self.header))

        self.rendertotal(tot)
        yrtot = len(set(o['yearID'] for o in self.stats))
        tot['INFO'] = '{:2} Season Total'.format(yrtot)
        print(self.fmt.format(**tot))
        
        self.rendertotal(n162)
        n162['INFO'] = '162 Game Ave.'
        print(self.fmt.format(**n162))

    def rendereach(self, eachstats):
        return {}

    def rendertotal(self, total):
        return {}


class ViewPitchingStats(ViewStats):

    header = ('  YR AGE  TM LG   W   L    ERA   G  GS  CG  SV    IP'
              '      H    R   ER   HR   BB   SO')
    fmt = ('{INFO:>15} {W:3.0f} {L:3.0f}'
           ' {ERA:6.2f} {G:3.0f} {GS:3.0f} {CG:3.0f} {SV:3.0f} {IP:>7}'
           ' {H:4.0f} {R:4.0f} {ER:4.0f} {HR:4.0f} {BB:4.0f} {SO:4.0f}')

    def compute_total(self):
        return TotPitching.normal(self.stats)

    def compute_per_season(self, total):
        # compute 162 G ave (following baseball-reference.com convention)
        n162 = {}
        for col in TotPitching.fields:
            n162[col] = 68. * total[col] / (total['G'] + total['GS'])
        return n162

    def rendereach(self, eachstats):
        s = eachstats
        o = {}
        for n in s.dtype.names:
            o[n] = s[n]
        o['age'] = self.playerdata.age(o['yearID'])
        o['INFO'] = ('{yearID:4d} {age:3d} {teamID:3s} {lgID:2s}'
                     .format(**o))
        o['ERA'] = 27. * o['ER'] / o['IPouts']
        o['IP'] = outs2inn(o['IPouts'])
        return o

    def rendertotal(self, total):
        o = total
        o['ERA'] = 27. * o['ER'] / o['IPouts']
        o['IP'] = outs2inn(o['IPouts'])
        return o


def fmtrate(r):
    return (' ---' if r is None
            else (('{:.3f}'.format(r))[1:] if r < 1
                  else ('{:.3f}'.format(r))[:4]))

def rate(x, y):
    return 1. * x / y if abs(y) > 0 else None


class ViewBattingStats(ViewStats):

    header = ('  YR AGE  TM LG'
              '    G    AB    R    H  2B  3B  HR  RBI'
              '  SB  CS   BB   SO'
              '   BA  OBP  SLG  OPS')
    fmt = ('{INFO:>15} {G:4.0f} {AB:5.0f} {R:4.0f} {H:4.0f} {2B:3.0f} {3B:3.0f}'
           ' {HR:3.0f} {RBI:4.0f} {SB:3.0f} {CS:3.0f} {BB:4.0f} {SO:4.0f}'
           ' {BA:4s} {OBP:4s} {SLG:4s} {OPS:4s}')

    def compute_total(self):
        return TotBatting.normal(self.stats)

    def compute_per_season(self, total):
        # compute 162 G ave (following baseball-reference.com convention)
        n162 = {}
        for col in TotBatting.fields:
            n162[col] = 162. * total[col] / total['G']
        return n162

    def rendereach(self, eachstats):
        s = eachstats
        o = {}
        for n in s.dtype.names:
            o[n] = s[n]
        o['age'] = self.playerdata.age(o['yearID'])
        o['INFO'] = ('{yearID:4d} {age:3d} {teamID:3s} {lgID:2s}'.format(**o))
        o['BA'] = fmtrate(rate(o['H'], o['AB']))
        obp = rate(o['H'] + o['BB'] + o['HBP'],
                   o['AB'] + o['BB'] + o['HBP'] + o['SF'])
        o['OBP'] = fmtrate(obp)
        slg = rate(o['H'] + 2. * o['2B'] + 3. * o['3B'] + 4. * o['HR'],
                   o['AB'])
        o['SLG'] = fmtrate(slg)
        o['OPS'] = fmtrate(None if None in (obp, slg) else obp + slg)
        return o

    def rendertotal(self, total):
        o = total
        o['BA'] = fmtrate(rate(o['H'], o['AB']))
        obp = rate(o['H'] + o['BB'] + o['HBP'],
                   o['AB'] + o['BB'] + o['HBP'] + o['SF'])
        o['OBP'] = fmtrate(obp)
        slg = rate(o['H'] + 2. * o['2B'] + 3. * o['3B'] + 4. * o['HR'],
                   o['AB'])
        o['SLG'] = fmtrate(slg)
        o['OPS'] = fmtrate(None if None in (obp, slg) else obp + slg)
        return o


class ViewFieldingStats(ViewStats):

    header = ('  YR AGE  TM LG POS    G   GS   INN      PO    A   E   DP'
              '  PB  WP   SB   CS')
    fmt = ('{INFO:>19} {G:4.0f} {GS:4.0f} {INN:>7s} {PO:5.0f}'
           ' {A:4.0f} {E:3.0f} {DP:4.0f} {PB:3.0f} {WP:3.0f} {SB:4.0f}'
           ' {CS:4.0f}')

    def compute_total(self):
        return TotFielding.normal(self.stats)

    def compute_per_season(self, total):
        # compute 162 G ave (following baseball-reference.com convention)
        n162 = {}
        for col in TotFielding.fields:
            n162[col] = 162. * total[col] / total['G']
        return n162

    def rendereach(self, eachstats):
        s = eachstats
        o = {}
        for n in s.dtype.names:
            o[n] = s[n]
        o['age'] = self.playerdata.age(o['yearID'])
        o['INFO'] = ('{yearID:4d} {age:3d} {teamID:3s}'
                     ' {lgID:2s} {POS:3s}'.format(**o))
        o['INN'] = outs2inn(o['InnOuts'])
        return o

    def rendertotal(self, total):
        o = total
        o['INN'] = outs2inn(o['InnOuts'])
        return o


class ViewAppearancesStats(ViewStats):

    header = ('  YR AGE  TM LG'
              '    G   GS  BAT  DEF    P    C   1B   2B   3B   SS'
              '   LF   CF   RF   OF   DH')
    fmt = ('{INFO:>15}'
           ' {G_all:4.0f} {GS:4.0f} {G_batting:4.0f} {G_defense:4.0f} {G_p:4.0f} {G_c:4.0f} {G_1b:4.0f} {G_2b:4.0f} {G_3b:4.0f}'
           ' {G_ss:4.0f} {G_lf:4.0f} {G_cf:4.0f} {G_rf:4.0f} {G_of:4.0f} {G_dh:4.0f}')

    def compute_total(self):
        return TotAppearances.normal(self.stats)

    def compute_per_season(self, total):
        # compute 162 G ave (following baseball-reference.com convention)
        n162 = {}
        for col in TotAppearances.fields:
            n162[col] = 162. * total[col] / total['G_all']
        return n162

    def rendereach(self, eachstats):
        s = eachstats
        o = {}
        for n in s.dtype.names:
            o[n] = s[n]
        o['age'] = self.playerdata.age(o['yearID'])
        o['INFO'] = ('{yearID:4d} {age:3d} {teamID:3s} {lgID:2s}'.format(**o))
        return o

    def rendertotal(self, total):
        return total


def showstats(pd):
    if len(pd.pitching):
        print('PITCHING\n')
        v = ViewPitchingStats(pd, pd.pitching)
        v.render()
        print()
    if len(pd.batting):
        print('BATTING\n')
        v = ViewBattingStats(pd, pd.batting)
        v.render()
        print()
    if len(pd.fielding):
        print('FIELDING\n')
        v = ViewFieldingStats(pd, pd.fielding)
        v.render()
        print()
    if len(pd.appearances):
        print('APPEARANCES\n')
        v = ViewAppearancesStats(pd, pd.appearances)
        v.render()


def showratings(attr):
    print('FNM        LNM           HT     WT  PO1  PO2       T  B    USB')
    print('{FNM:<10s} {LNM:<10s}   {HT:5s}  {WT:3d}   {PO1:4s} {PO2:4s}'
          '     {T:1s}  {B:1s}      {USB:1s}'
          .format(**attr))
    print()

    if attr['PO1'] in ['SP', 'RP', 'CP']:
        print('STA  PCL   H9  HR9   K9  BB9')
        print(' {STA:2d}   {PCL:2d}   {H9:2d}   {HR9:2d}   {K9:2d}   {BB9:2d}'
              .format(**attr))
        print()

        h, s = '', ''
        for i in range(1, 6):
            key = 'P{:d}'.format(i)
            if len(attr[key]) == 0:
                continue
            h += '  P{i:d} P{i:d}S P{i:d}C P{i:d}B '.format(i=i)
            s += ('{:4s}  {:2d}  {:2d}  {:2d} '
                  .format(attr[key], attr[key + 'S'], attr[key +'C'],
                          attr[key + 'B']))
        if h and s:
            print(h)
            print(s)
            print()

    print('RCT  LCT  RPW  LPW  BNT  DBN  VIS  DIS'
          '  CLU  DUR  SPD  AMS  AMA  REA  FLD  BLK  BAB  BAG')
    print(' {RCT:2d}   {LCT:2d}   {RPW:2d}   {LPW:2d}   {BNT:2d}   {DBN:2d}'
          '   {VIS:2d}   {DIS:2d}   {CLU:2d}   {DUR:2d}   {SPD:2d}   {AMS:2d}'
          '   {AMA:2d}   {REA:2d}   {FLD:2d}   {BLK:2d}   {BAB:2d}   {BAG:2d}'
          .format(**attr))
