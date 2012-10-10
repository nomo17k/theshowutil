#!/usr/bin/env python2.7
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
#from __future__ import unicode_literals
from math import exp, sqrt


def argsort(seq):
    """Emulate NumPy argsort"""
    return sorted(range(len(seq)), key=seq.__getitem__)


class require(object):

    def __init__(self, *args, **kwargs):
        self.requires = args
        self.retval = kwargs.get('retval', -1)

    def __call__(self, originalfunc):
        decoratorself = self
        def wrappee(s, *args, **kwargs):
            requires = decoratorself.requires
            if requires:
                for r in requires:
                    if len(s.stats[r]) == 0:
                        return decoratorself.retval
            return originalfunc(s, *args, **kwargs)
        return wrappee


def keeprange(fn):
    def _f(s, *args, **kwargs):
        r = fn(s, *args, **kwargs)
        if r == -1:
            return -1
        r = int(round(r))
        return r if 0 <= r <= 99 else (0 if r < 0 else 99)
    return _f


def div(a, b):
    return a / b if b != 0 else 0.


class RatingGenerator(object):

    def __init__(self, attr, stats):
        self.stats = stats
        self.attr = attr

    def rate(self):
        a = self.attr
        a['PO1'], a['PO2'] = self.find_positions()

        a['STA'] = self.rate_stamina()
        a['PCL'] = self.rate_pitchingclutch()
        a['K9'] = self.rate_k9()
        a['BB9'] = self.rate_bb9()
        a['H9'] = self.rate_h9()
        a['HR9'] = self.rate_hr9()

        a['RCT'] = self.rate_contact()
        a['LCT'] = self.rate_contact()
        a['RPW'] = self.rate_power()
        a['LPW'] = self.rate_power()
        a['BNT'] = self.rate_buntingability()
        a['DBN'] = self.rate_dragbunting()
        a['VIS'] = self.rate_platevision()
        a['DIS'] = self.rate_platediscipline()
        a['CLU'] = self.rate_clutch()
        a['DUR'] = self.rate_durability()
        a['SPD'] = self.rate_speed(pos=a['PO1'])
        a['BAB'] = self.rate_brability()
        a['BAG'] = self.rate_braggressiveness()

        return a

    def rate_stamina(self, *args, **kwargs): return -1
    def rate_pitchingclutch(self, *args, **kwargs): return -1
    def rate_k9(self, *args, **kwargs): return -1
    def rate_bb9(self, *args, **kwargs): return -1
    def rate_h9(self, *args, **kwargs): return -1
    def rate_hr9(self, *args, **kwargs): return -1
    def rate_contact(self, *args, **kwargs): return -1
    def rate_power(self, *args, **kwargs): return -1
    def rate_buntingability(self, *args, **kwargs): return -1
    def rate_dragbunting(self, *args, **kwargs): return -1
    def rate_platevision(self, *args, **kwargs): return -1
    def rate_platediscipline(self, *args, **kwargs): return -1
    def rate_clutch(self, *args, **kwargs): return -1
    def rate_durability(self, *args, **kwargs): return -1
    def rate_speed(self, *args, **kwargs): return -1
    def rate_brability(self, *args, **kwargs): return -1
    def rate_braggressiveness(self, *args, **kwargs): return -1
    def find_positions(self): return ('', '')


class BasicRatingGenerator(RatingGenerator):

    def rate(self):
        a = super(BasicRatingGenerator, self).rate()
        a['RCT'] = self.rate_contact(bat=a['B'], vs='R', displ=a['DIS'])
        a['LCT'] = self.rate_contact(bat=a['B'], vs='L', displ=a['DIS'])
        a['RPW'] = self.rate_power(bat=a['B'], vs='R')
        a['LPW'] = self.rate_power(bat=a['B'], vs='L')
        return a

    @keeprange
    @require('pitching')
    def rate_stamina(self, *args, **kwargs):
        s = self.stats['pitching']
        if self.attr['PO1'] == 'SP':
            x = (s['IPouts'] / 3. / s['GS'])
            r = (100. - 60.) / (7.7 - 4.3) * (x - 4.3) + 60.
            r = max(r, 60.)
        elif self.attr['PO1'] in ('RP', 'CP'):
            x = (s['IPouts'] / 3. / s['G'])
            r = (50. - 15.) / (2.0 - 0.5) * (x - 1.0) + 28.
            r = max(r, 15.)
        else:
            r = -1
        return r

    @keeprange
    @require('pitching')
    def rate_pitchingclutch(self, *args, **kwargs):
        return 54

    @keeprange
    @require('pitching')
    def rate_k9(self, *args, **kwargs):
        s = self.stats['pitching']
        so, out = s.get('SO', -1), s.get('IPouts', -1)
        if not (out > 0):
            return -1
        k9 = 27. * so / out
        return (k9 + 0.6519) / 0.1139

    @keeprange
    @require('pitching')
    def rate_bb9(self, *args, **kwargs):
        s = self.stats['pitching']
        bb, tbf = s.get('BB', -1), s.get('BFP', -1)
        if not (tbf > 0):
            return -1
        rr = bb / tbf
        return (rr - 0.1309) / -0.0007

    @keeprange
    @require('pitching')
    def rate_h9(self, *args, **kwargs):
        s = self.stats['pitching']
        h, ab  = s['H'], s['BFP'] - s['BB'] -s['HBP'] -s['SF'] -s['SH']
        if not (ab > 0):
            return -1
        ba = h / ab
        return (ba - 0.3477) / -0.0014

    @keeprange
    @require('pitching')
    def rate_hr9(self, *args, **kwargs):
        s = self.stats['pitching']
        hr, h  = s['HR'], s['H']
        if not (h > 0):
            return -1
        x = 1. * hr / h
        r = (x - 0.11) * (100. - 20.) / (0.05 - 0.17) + 60.
        r = max(r, 20.)
        return r

    @keeprange
    @require('batting')
    def rate_contact(self, bat='R', vs='R', displ=40, psig=0., *args, **kwargs):
        s = self.stats['batting']
        
        h, ab = s['H'], s['AB']
        if not (ab > 0):
            return -1
        # generic ratio for (AB vs LHP) / (AB vs RHP)
        r = .50786 if bat == 'R' else 0.21818

        # platoon advantage: [(OBA vs LHP) - (OBA vs RHP)] / (OBA total)
        # for RHB.
        pltp = {'R': 0.0514, 'L': -0.0833, 'S': 0.0000}[bat]

        # std dev
        spltp = {'R': 0.0420, 'L': 0.0458, 'S': 0.0640}[bat]
        pltp += spltp * psig if bat == 'R' else -spltp * psig
        
        ba = (1.*h / ab * (1 + r * (1 - pltp)) / (1 + r) if vs == 'R'
              else (1.*h / ab * (r + 1 + pltp)) / (1 + r))
        return ((1. * ba - 0.1838 - 1.965e-4 * displ)
                / (1.034e-3 + 1.508e-6 * displ))

    @keeprange
    @require('batting')
    def rate_power(self, bat='R', vs='R', psig=0., *args, **kwargs):
        s = self.stats['batting']

        h, hr = s['H'], s['HR'] 
        if not (h > 0):
            return -1

        # generic ratio for (AB vs LHP) / (AB vs RHP)
        r = .50786 if bat == 'R' else 0.21818

        # platoon advantage: [(OBA vs LHP) - (OBA vs RHP)] / (OBA total)
        # for RHB.
        pltp = {'R': 0.0095, 'L': -0.0520, 'S': 0.000}[bat]
        
        # std dev
        spltp = {'R': 0.0420, 'L': 0.0458, 'S': 0.0640}[bat]
        pltp += spltp * psig if bat == 'R' else -spltp * psig

        hrph = (1.*hr / h * (1 + r * (1 - pltp)) / (1 + r) if vs == 'R'
                else (1.*hr / h * (r + 1 + pltp)) / (1 + r))
        return (hrph + 0.06375) / 3.350e-3

    @keeprange
    @require('batting')
    def rate_buntingability(self, *args, **kwargs):
        s = self.stats['batting']
        sh, pa = s['SH'], s['AB'] + s['BB'] + s['SH'] + s['SF'] + s['HBP']
        shpa = (div(1. * sh, pa) / 12. if self.attr['PO1'] in ('SP','RP','CP')
                else 1. * div(sh, pa))
        if not (pa > 0):
            return -1
        return 93. * (1. - exp(-80. * (shpa)))

    @keeprange
    @require('batting')
    def rate_dragbunting(self, *args, **kwargs):
        s = self.stats['batting']
        sh, pa = s['SH'], s['AB'] + s['BB'] + s['SH'] + s['SF'] + s['HBP']
        if not (pa > 0):
            return -1
        return 96. * (1. - exp(-60. * ((1. * sh / pa) - 0.002)))

    @keeprange
    @require('batting')
    def rate_platevision(self, *args, **kwargs):
        s = self.stats['batting']
        so, ab = s['SO'], s['AB']
        if not (ab > 0):
            return -1
        return - ((1. * so / ab) - 0.2884) / 1.6732e-3

    @keeprange
    @require('batting')
    def rate_platediscipline(self, *args, **kwargs):
        s = self.stats['batting']
        bb, pa = s['BB'], s['AB'] + s['BB'] + s['HBP'] + s['SH'] + s['SF']
        if not (pa > 0):
            return -1
        return (771.1 * (bb / pa))

    @keeprange
    @require('batting')
    def rate_clutch(self, *args, **kwargs):
        return 70.

    @keeprange
    @require('batting', 'fielding', 'appearances')
    def rate_durability(self, *args, **kwargs):
        s = self.stats['appearances']
        g_all, gs, gp = s['G_all'], s['GS'], s['G_p']
        yrtot = s['YR_TOT']

        if self.attr['PO1'] == 'SP':
            return 55. * gs / yrtot / 36. + 45.
        elif self.attr['PO1'] == 'RP':
            return 70. * gp / yrtot / 80. + 30.
        elif self.attr['PO1'] == 'CP':
            return 55. * gp / yrtot / 50. + 45.

        s = self.stats['fielding']
        innouts = s['InnOuts']

        s = self.stats['batting']
        pa = sum([s[k] for k in ['AB', 'BB', 'IBB', 'HBP', 'SH', 'SF']])
        paneed = g_all * 3.1
        
        r = 1. * (innouts / 3.) / (g_all * 9.)
        
        if 1. * gs / g_all > 0.8:
            # starter...
            gsf = (innouts / 3.) / (g_all * 9.)
            r1 = (45. if gsf < .75
                  else ((gsf - .75)*(95. - 45.)/(.9 - .75) + 45 if gsf < .9
                        else (gsf - .95)*(99. - 95.)/(1. - .95) + 95))
            r2 = 70. * g_all / (yrtot * 162.) + 30.
            r = min(r1, r2)
        else:
            # bench player...
            r = 70. * g_all / (yrtot * 162.) + 30.
        return r

    @keeprange
    @require('batting', 'fielding')
    def rate_speed(self, *args, **kwargs):
        pos = kwargs.get('pos', None)
        s = self.stats['batting']
        sb, cs = 1. * s['SB'], 1. * s['CS']
        h, h2, h3, hr = 1. * s['H'], 1. * s['2B'], 1. * s['3B'], 1. * s['HR']
        ab, so, bb = 1.*s['AB'], 1.*s['SO'], 1.*s['BB']
        r, hbp, gidp = 1.*s['R'], 1.*s['HBP'], 1.*s['GIDP']

        s = self.stats['fielding']
        po, a, g = 1. * s['PO'], 1. * s['A'], 1. * s['G']

        f1 = (sb + 3.0) / (sb + cs + 7.0)
        f1 = (f1 - 0.4) * 20.
        f2 = div((sb + cs) , ((h - h2 - h3 - hr) + bb + hbp))
        f2 = sqrt(f2) / 0.07
        f3 = div(h3 , (ab - hr - so))
        f3 = f3 / 0.0016
        f4 = div((r - hr) , (h + bb + hbp - hr))
        f4 = (f4 - 0.1) * 25.
        f5 = div(gidp , (ab - hr - so))
        f5 = (0.063 - f5) / 0.007
        f6 = {None: 0, '': 0,
              'SP': 0., 'RP': 0., 'CP': 0.,
              'C': 1.,
              '1B': 2.,
              '2B': (((po + a) / g) / 4.8) * 6.,
              '3B': (((po + a) / g) / 2.65) * 4.,
              'SS': (((po + a) / g) / 4.6) * 7.,
              'LF': (((po + a) / g) / 2.0) * 6.,
              'CF': (((po + a) / g) / 2.0) * 6.,
              'RF': (((po + a) / g) / 2.0) * 6.,
              'OF': (((po + a) / g) / 2.0) * 6.}[pos]

        ss = [max(min(float(f), 10.), 0.) for f in [f1, f2, f3, f4, f5, f6]]
        ss = float(sum(ss) / len(ss))
        r = ((ss - 1.531) / 1.498e-3)**(1./1.822) if ss > 1.531 else 0.
        return r

    @keeprange
    @require('batting')
    def rate_brability(self, *args, **kwargs):
        s = self.stats['batting']
        sb, cs = s['SB'], s['CS']
        if not (sb + cs > 0):
            return -1
        sbp = 1. * sb / (sb + cs)
        return ((sbp * 100 - 52.3) / 0.3525)

    @keeprange
    @require('batting')
    def rate_braggressiveness(self, *args, **kwargs):
        s = self.stats['batting']
        sb, cs, h, bb, hbp = s['SB'], s['CS'], s['H'], s['BB'], s['HBP']
        if not (h + bb + hbp > 0):
            return -1
        sbr = 1. * (sb + cs) / (h + bb + hbp)
        return ((sbr + .02169) / 0.003397)

    @require('appearances', retval=('', ''))
    def find_positions(self):
        stats = self.stats

        s = stats['appearances']
        posstr = ['P', 'C', '1B', '2B', '3B', 'SS', 'LF', 'CF', 'RF']
        gs = [s['G_p'], s['G_c'], s['G_1b'],
              s['G_2b'], s['G_3b'], s['G_ss'],
              s['G_lf'], s['G_cf'], s['G_rf']]
        if sum(gs) == 0:
            # likely a DH; need to decide from defensive spectrum
            return ('LF', '1B')

        idxsorted = argsort(gs)[::-1]
        pos1 = idxsorted[0]

        if pos1 == 0:
            # this is a pitcher, so choose one of SP, RP, and CP:
            p = stats['pitching']
            if len(p) == 0:
                return ('', '')
            if (1. * p['GS']) / p['G'] > .5:
                return ('SP', '')
            else:
                return ('CP' if p['SV'] > p['G'] * .3 else 'RP', '')

        if gs[idxsorted[1]] == 0:
            return (posstr[pos1], '')
        if gs[idxsorted[2]] == 0:
            return (posstr[pos1], posstr[idxsorted[1]])

        # below, we are dealing with a case in which more than two
        # positions have been played by this player.
        nif = sum(gs[2:6]) if len([1 for x in gs[2:6] if x > 0]) == 4 else 0
        nof = sum(gs[6:9]) if len([1 for x in gs[6:9] if x > 0]) == 3 else 0
        if nif > 0 and nif >= nof:
            return (posstr[pos1], 'IF')
        if nof > 0 and nof > nif:
            return (posstr[pos1], 'OF')
        if pos1 not in [3, 5] and gs[3] > 0 and gs[5] > 0:
            return (posstr[pos1], '2B/SS')
        if pos1 not in [2, 4] and gs[2] > 0 and gs[4] > 0:
            return (posstr[pos1], '1B/3B')
        if pos1 not in [1, 2] and gs[1] > 0 and gs[2] > 0:
            return (posstr[pos1], 'C/1B')
        if pos1 not in [1, 4] and gs[1] > 0 and gs[4] > 0:
            return (posstr[pos1], 'C/3B')
        return (posstr[pos1], posstr[idxsorted[1]])
