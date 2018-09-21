"""
lexer and parser specification for aggregate
============================================

Overview
--------

Ignored colon, comma, ( ) |

A markdown pipe table: ignores pipes and first two rows

Valid program

| name        | expos                 | limit                    | sev                                               | freq              |
|:------------|:----------------------|:-------------------------|:--------------------------------------------------|:------------------|
| big_mixture | 50 claims             | [50, 100, 150, 200] xs 0 | on lognorm 12 cv [1,2,3,4] wts [0.25 .25 .25 .25] | poisson           |
| A1          | 500 premium at 0.5    |                          | on gamma 12 cv .30                                | mixed gamma 0.014 |
| A1          | 500 premium at 0.5 lr |                          | on gamma 12 cv .30                                | mixed gamma 0.014 |
| A2          | 50  claims            | 30 xs 10                 | on gamma 12 cv .30                                | mixed gamma 0.014 |
| A3          | 50  claims            |                          | on gamma 12 cv .30                                | mixed gamma 0.014 |
| A4          | 50  claims            | 30 xs 20                 | on gamma 12 cv .30                                | mixed gamma 0.14  |
| hcmp        | 1000 * uw.cmp         |                          |                                                   |                   |
| incmp       | uw.cmp * 0.001        |                          |                                                   |                   |

Language Specification
----------------------

answer              	:: sev_out
                    	 | agg_out

port_out            	:: port_name agg_list

agg_list            	:: agg_list agg_out

sev_out             	:: sev_out sev_name sev

freq                	:: FIXED
                    	 | POISSON

sev                 	:: sev PLUS numbers
                    	 | sev MINUS numbers
                    	 | ids numbers CV numbers weights
                    	 | ids xps

xps                 	:: XPS numbers numbers
                    	 | 

weights             	:: WEIGHTS EQUAL_WEIGHT NUMBER
                    	 | WEIGHTS numbers
                    	 | 

layers              	:: numbers XS numbers

exposures           	:: numbers CLAIMS
                    	 | numbers LOSS
                    	 | numbers PREMIUM AT numbers LR

ids                 	:: "[" idl "]"
                    	 | ID

idl                 	:: idl ID
                    	 | ID

numbers             	:: "[" numberl "]"

numberl             	:: numberl NUMBER
                    	 | NUMBER

builtin_aggregate   	:: builtin_aggregate_dist TIMES NUMBER
                    	 | builtin_aggregate_dist

sev_name            	:: SEV ID

parser.out parser debug information
-----------------------------------

Grammar:

Rule 0     S' -> ans
Rule 1     ans -> name exposures layers sev_term freq
Rule 2     ans -> name builtin_aggregate
Rule 3     freq -> <empty>
Rule 4     freq -> POISSON
Rule 5     freq -> FIXED
Rule 6     freq -> MIXED ids numbers
Rule 7     freq -> MIXED ids numbers numbers
Rule 8     sev_term -> ON sev
Rule 9     sev -> builtinids
Rule 10    sev -> ids numbers numbers weights xps
Rule 11    sev -> ids numbers weights
Rule 12    sev -> ids numbers CV numbers weights
Rule 13    sev -> numbers TIMES sev  [precedence=left, level=2]
Rule 14    sev -> sev MINUS numbers  [precedence=left, level=1]
Rule 15    sev -> sev PLUS numbers  [precedence=left, level=1]
Rule 16    xps -> <empty>
Rule 17    xps -> XPS numbers numbers
Rule 18    weights -> <empty>
Rule 19    weights -> WEIGHTS numbers
Rule 20    layers -> <empty>
Rule 21    layers -> numbers XS numbers
Rule 22    exposures -> numbers PREMIUM AT numbers
Rule 23    exposures -> numbers PREMIUM AT numbers LR
Rule 24    exposures -> numbers LOSS
Rule 25    exposures -> numbers CLAIMS
Rule 26    builtinids -> BUILTINID
Rule 27    builtinids -> [ builtinidl ]
Rule 28    builtinidl -> BUILTINID
Rule 29    builtinidl -> builtinidl BUILTINID
Rule 30    ids -> ID
Rule 31    ids -> [ idl ]
Rule 32    idl -> ID
Rule 33    idl -> idl ID
Rule 34    numbers -> NUMBER
Rule 35    numbers -> [ numberl ]
Rule 36    numberl -> NUMBER
Rule 37    numberl -> numberl NUMBER
Rule 38    builtin_aggregate -> BUILTINID
Rule 39    builtin_aggregate -> NUMBER TIMES BUILTINID
Rule 40    builtin_aggregate -> BUILTINID TIMES NUMBER
Rule 41    name -> ID

Terminals, with rules where they appear:

AT                   : 22 23
BUILTINID            : 26 28 29 38 39 40
CLAIMS               : 25
CV                   : 12
FIXED                : 5
ID                   : 30 32 33 41
LOSS                 : 24
LR                   : 23
MINUS                : 14
MIXED                : 6 7
NUMBER               : 34 36 37 39 40
ON                   : 8
PLUS                 : 15
POISSON              : 4
PREMIUM              : 22 23
TIMES                : 13 39 40
WEIGHTS              : 19
XPS                  : 17
XS                   : 21
[                    : 27 31 35
]                    : 27 31 35
error                :

Nonterminals, with rules where they appear:

ans                  : 0
builtin_aggregate    : 2
builtinidl           : 27 29
builtinids           : 9
exposures            : 1
freq                 : 1
idl                  : 31 33
ids                  : 6 7 10 11 12
layers               : 1
name                 : 1 2
numberl              : 35 37
numbers              : 6 7 7 10 10 11 12 12 13 14 15 17 17 19 21 21 22 22 23 23 24 25
sev                  : 8 13 14 15
sev_term             : 1
weights              : 10 11 12
xps                  : 10

Lexer term definition
---------------------


    tokens = {ID, PLUS, MINUS, TIMES, NUMBER, CV, LOSS, PREMIUM, AT, LR, CLAIMS, XS, MIXED,
              FIXED, POISSON, BUILTINID, WEIGHTS, XPS, ON}
    ignore = ' \t,\\:\\(\\)|'
    literals = {'[', ']'}

    BUILTINID = r'uw\.[a-zA-Z_][a-zA-Z0-9_]*'
    ID = r'[a-zA-Z_][a-zA-Z0-9_]*'
    PLUS = r'\+'
    MINUS = r'\-'
    TIMES = r'\*'
    ID['loss'] = LOSS
    ID['at'] = AT
    ID['cv'] = CV
    ID['premium'] = PREMIUM
    ID['prem'] = PREMIUM
    ID['lr'] = LR
    ID['on'] = ON
    ID['claims'] = CLAIMS
    ID['claim'] = CLAIMS
    ID['xs'] = XS
    ID['wts'] = WEIGHTS
    ID['xps'] = XPS
    ID['mixed'] = MIXED
    ID['poisson'] = POISSON
    ID['fixed'] = FIXED
    ID['inf'] = NUMBER

Testing Code
------------


    from aggregate.underwriter import Underwriter
    uu = Underwriter(debug=True)

    # test cases

    uw.test_write('myname: 100 premium at .4 lr lognorm 12 .3')
    uw.test_write('myname: 100 premium at .4 lr lognorm 12 cv .3')
    uw.test_write('myname: uw.cmp')
    uw.test_write('mycmp: uw.cmp; my1000cmp: 1000 * uw.cmp; mycmp1000 uw.cmp*0.001')
    uw.test_write('myname:  uw.cmp * 0.000001')

    uw.test_write('''A: 500 premium at 0.5   gamma 12 cv .30 (mixed gamma 0.014)
    A1: 500 premium at 0.5 lr  gamma 12 cv .30 (mixed gamma 0.014)
    A2: 50  claims 30 xs 10  gamma 12 cv .30 (mixed gamma 0.014)
    A3: 50  claims    gamma 12 cv .30 (mixed gamma 0.014)
    A4: 50  claims 30 xs 20  gamma 12 cv .30 (mixed gamma 0.14)
    cmp: 1000 * uw.cmp''')

    uw.test_write(''' B 15 claims 15 xs 15 lognorm 12 cv 1.5 + 2 mixed gamma 4.8
    Cat 1.7 claims 25 xs 5 25 * pareto 1.3 0 - 25 poisson ''')

    uw.test_write('weighted 1000 loss 500 xs 100 lognorm 12 [0.3, 0.5, 0.9] wts [.3333, .3333, .3334] ')


References
----------

https://sly.readthedocs.io/en/latest/sly.html

"""
from sly import Lexer, Parser
import logging
import numpy as np
from collections import Iterable


class UnderwritingLexer(Lexer):
    tokens = {ID, BUILTINID,
              SEV, AGG, PORT,
              PLUS, MINUS, TIMES, NUMBER,
              LOSS, PREMIUM, AT, LR, CLAIMS,
              XS,
              CV, WEIGHTS, EQUAL_WEIGHT, XPS,
              MIXED, FIXED, POISSON
              }
    ignore = ' \t,\\:\\(\\)|'
    literals = {'[', ']'}

    BUILTINID = r'uw\.[a-zA-Z][a-zA-Z0-9_]*'
    ID = r'[a-zA-Z][a-zA-Z0-9_]*'
    PLUS = r'\+'
    MINUS = r'\-'
    TIMES = r'\*'
    EQUAL_WEIGHT = r'='
    ID['loss'] = LOSS
    ID['at'] = AT
    ID['cv'] = CV
    ID['prem'] = PREMIUM
    ID['premium'] = PREMIUM
    ID['lr'] = LR
    ID['claim'] = CLAIMS
    ID['claims'] = CLAIMS
    ID['x'] = XS
    ID['xs'] = XS
    ID['wts'] = WEIGHTS
    ID['wt'] = WEIGHTS
    ID['xps'] = XPS
    ID['mixed'] = MIXED
    ID['poisson'] = POISSON
    ID['fixed'] = FIXED
    ID['inf'] = NUMBER
    ID['sev'] = SEV
    ID['on'] = SEV
    ID['agg'] = AGG
    ID['port'] = PORT

    @_(r'\-?(\d+\.?\d*|\d*\.\d+)([eE](\+|\-)?\d+)?')
    def NUMBER(self, t):
        if t.value == 'INF' or t.value == 'inf':
            t.value = np.inf
        else:
            t.value = float(t.value)
        return t

    @_(r'\n+')
    def newline(self, t):
        self.lineno += t.value.count('\n')

    def error(self, t):
        print(f"Illegal character '{t.value[0]:s}'")
        self.index += 1


class UnderwritingParser(Parser):
    # debugfile = 'parser.out'
    tokens = UnderwritingLexer.tokens
    precedence = (('left', PLUS, MINUS), ('left', TIMES))

    def __init__(self, safe_lookup_function, debug=False):
        self.arg_dict = None
        self.sev_out_dict = None
        self.agg_out_dict = None
        self.port_out_dict = None
        self.reset()
        # instance of uw class to look up severities
        self._safe_lookup = safe_lookup_function
        if debug:
            def _print(s):
                print(s)

            self.p = _print
        else:
            def _print(s):
                logging.info('UnderwritingParser | ' + s)

            self.p = _print

    def reset(self):
        # TODO Add sev_xs and sev_ps !!
        self.sev_out_dict = {}
        self.agg_out_dict = {}
        self.port_out_dict = {}

    @staticmethod
    def _check_vectorizable(value):
        """
        check the if value can be vectorized

        """
        if isinstance(value, float) or isinstance(value, int) or isinstance(value, np.ndarray):
            return value
        else:
            return np.array(value)

            # @staticmethod
    # def new_arg_dict():
    #     # to
    #     # in order to allow for missing terms this must reflect sensible defaults
    #     return dict(name="", exp_el=0, exp_premium=0, exp_lr=0, exp_en=0, exp_attachment=0, exp_limit=np.inf,
    #                 sev_name='', sev_a=0, sev_b=0, sev_mean=0, sev_cv=0, sev_scale=0, sev_loc=0, sev_wt=1,
    #                 freq_name='poisson', freq_a=0, freq_b=0)

    # final answer exit points ===================================
    @_('sev_out')
    def answer(self, p):
        self.p(f'\t\tExiting through sev_out, created severity {p.sev_out}')

    @_('agg_out')
    def answer(self, p):
        self.p(f'\t\tExiting through agg_out, created aggregate {p.agg_out}')

    @_('port_out')
    def answer(self, p):
        self.p(f'\t\tExiting through port_out, portfolio has {len(self.port_out_dict)} aggregates')

    # building portfolios =======================================
    @_('port_name agg_list')
    def port_out(self, p):
        self.p(f'\tport_name and agg_list to port_out {p.port_name}')
        self.port_out_dict[p.port_name] = p.agg_list

    @_('agg_list agg_out')
    def agg_list(self, p):
        self.p(f'\tadding agg_out {p.agg_out} to agg_list {p.agg_list}')
        if p.agg_list is None:
            raise ValueError('ODD agg list is empty')
        p.agg_list.append(p.agg_out)
        return p.agg_list

    @_('agg_out')
    def agg_list(self, p):
        self.p(f'\tadding agg_out {p.agg_out} to new agg_list')
        return [p.agg_out]

    # building aggregates ========================================
    @_('agg_name builtin_aggregate')
    def agg_out(self, p):
        self.p(f'agg_name builtin_aggregate {p.builtin_aggregate} to agg_out')
        self.agg_out_dict[p.agg_name] = {'name': p.agg_name, **p.builtin_aggregate}
        return p.agg_name

    # standard spec expos [layers] sevs [freq]
    @_('agg_name exposures layers SEV sev freq')
    def agg_out(self, p):
        self.p(f'agg_name exposures layers SEV sev freq to agg_out {p.agg_name}')
        self.agg_out_dict[p.agg_name] = {'name': p.agg_name, **p.exposures, **p.layers, **p.sev, **p.freq}
        return p.agg_name

    # building severities ======================================
    @_('sev_out sev_name sev')
    def sev_out(self, p):
        self.p(f'sev_out sev_name {p.sev_name} sev to sev_out, appending to sev_out_dict')
        self.sev_out_dict[p.sev_name] = p.sev

    @_('sev_name sev')
    def sev_out(self, p):
        self.p(f'sev_name sev resolving to sev_part {p.sev_name}, adding to sev_out_dict')
        self.sev_out_dict[p.sev_name] = p.sev

    # frequency term ==========================================
    # for all frequency distributions claim count is determined by exposure / severity
    # only freq shape parameters need be entered
    @_('MIXED ID numbers numbers')
    def freq(self, p):
        self.p(f'MIXED ids numbers numbers {p.ID}, {p.numbers}, {p.numbers} two param freq, numbers.1=CVs')
        return {'freq_name': p.ID, 'freq_a': p[2], 'freq_b': p[3]}  # TODO IDS--> poisson for now

    @_('MIXED ID numbers')
    def freq(self, p):
        self.p(f'MIXED ids numbers {p.ID}, {p.numbers} single param freq, numbers=CVs')
        # return {'freq_name': p.ids, 'freq_a': p.numbers}  # TODO IDS--> poisson for now
        return {'freq_name': 'poisson', 'freq_a': p.numbers}  # TODO IDS--> poisson for now

    @_('FIXED')
    def freq(self, p):
        self.p('FIXED')
        return {'freq_name': 'fixed'}

    @_('POISSON')
    def freq(self, p):
        self.p('POISSON')
        return {'freq_name': 'poisson'}

    @_('')
    def freq(self, p):
        self.p('missing frequency term')
        return { 'freq_name': 'poisson'}

    # severity term ============================================
    @_('sev PLUS numbers')
    def sev(self, p):
        self.p(f'resolving sev PLUS numbers to sev {p.numbers}')
        p.sev['sev_loc'] = UnderwritingParser._check_vectorizable(p.sev.get('sev_loc', 0))
        p.numbers = UnderwritingParser._check_vectorizable(p.numbers)
        p.sev['sev_loc'] += p.numbers
        return p.sev

    @_('sev MINUS numbers')
    def sev(self, p):
        self.p(f'resolving sev MINUS numbers to sev {p.numbers}')
        p.sev['sev_loc'] = p.sev.get('sev_loc', 0) - p.numbers
        return p.sev

    @_('numbers TIMES sev')
    def sev(self, p):
        self.p(f'resolving numbers TIMES sev to sev {p.numbers}')
        p.numbers = UnderwritingParser._check_vectorizable(p.numbers)
        if 'sev_mean' in p.sev:
            p.sev['sev_mean'] = UnderwritingParser._check_vectorizable(p.sev.get('sev_mean', 0))
            p.sev['sev_mean'] *= p.numbers
        # only scale scale if there is a scale (otherwise you double count)
        # TODO OK? sev_scale...
        if 'sev_scale' in p.sev:
            p.sev['sev_scale'] = UnderwritingParser._check_vectorizable(p.sev.get('sev_scale', 0))
            p.sev['sev_scale'] *= p.numbers
        if 'sev_mean' not in p.sev:
            # e.g. Pareto has no mean and it is important to set the scale
            # but if there is a mean it handles the scaling and setting scale will
            # confuse the distribution maker
            p.sev['sev_scale'] = p.numbers
        return p.sev

    @_('ids numbers CV numbers weights')
    def sev(self, p):
        self.p(f'resolving ids {p.ids} numbers CV numbers sev {p[1]}, {p[3]}')
        return {'sev_name':  p.ids, 'sev_mean':  p[1], 'sev_cv':  p[3], 'sev_wt': p.weights}

    @_('ids numbers weights')
    def sev(self, p):
        self.p(f'resolving ids {p.ids} numbers {p[1]} to sev (one param dist)')
        return {'sev_name': p.ids, 'sev_a':  p[1], 'sev_wt': p.weights}

    #                                v can go
    @_('ids numbers numbers weights xps')
    def sev(self, p):
        self.p(f'resolving ids {p.ids} numbers numbers {p[1]}, {p[2]} to sev (two param sev dist)')
        return {'sev_name': p.ids, 'sev_a':  p[1], 'sev_b':  p[2], 'sev_wt': p.weights, **p.xps}

    # TODO a bit restrictive on numerical densities here!
    #      v put in weights here instead (if xps relevant then cannot need shape parameters)
    @_('ids xps')
    def sev(self, p):
        self.p(f'resolving ids {p.ids} xps {p.xps} to sev (fixed or histogram type)')
        return {'sev_name': p.ids, **p.xps}

    @_('XPS numbers numbers')
    def xps(self, p):
        self.p(f'XPS numbers numbers resolving to xs and ps {p[1]}, {p[2]}')
        return {'sev_xs':  p[1], 'sev_ps':  p[2]}

    @_('')
    def xps(self, p):
        self.p('missing xps term')
        return {}

    @_('WEIGHTS EQUAL_WEIGHT NUMBER')
    def weights(self, p):
        self.p(f'WEIGHTS EQUAL_WEIGHTS {p.NUMBER} resolving to equal weights')
        return np.ones(int(p.NUMBER)) / p.NUMBER

    @_('WEIGHTS numbers')
    def weights(self, p):
        self.p(f'WEIGHTS numbers resolving to weights {p.numbers}')
        return p.numbers

    @_('')
    def weights(self, p):
        self.p('missing weights term')
        return 1

    @_('builtinids')
    def sev(self, p):
        self.p(f'builtinds {p.builtinids} to sev')
        # look up ID in uw
        return self._safe_lookup(p.builtinids, 'severity')
        # return self._safe_lookup(n, 'severity') for n in p.builtinids]
        # for n in p.builtinids:
        #     built_in_dict = self._safe_lookup(n, 'severity')
        #     self.arg_dict.update(built_in_dict)

    # layer terms, optoinal ===================================
    @_('numbers XS numbers')
    def layers(self, p):
        self.p(f'numbers XS numbers to layers {p[0]} xs {p[2]}')
        return {'exp_attachment': p[2], 'exp_limit': p[0]}

    @_('')
    def layers(self, p):
        self.p('missing layer term')
        return {}

    # exposures term ==========================================
    @_('numbers CLAIMS')
    def exposures(self, p):
        self.p(f'resolving numbers CLAIMS to exposures {p.numbers}')
        return {'exp_en': p.numbers}

    @_('numbers LOSS')
    def exposures(self, p):
        self.p(f'resolving numbers LOSS to exposures {p.numbers}')
        return {'exp_el': p.numbers}

    @_('numbers PREMIUM AT numbers LR')
    def exposures(self, p):
        self.p(f'resolving numbers PREMIUM AT numbers LR to exposures {p[0]} at {p[3]}')
        return {'exp_premium': p[0], 'exp_lr': p[3], 'exp_el': p[0] * p[3]}

    @_('numbers PREMIUM AT numbers')
    def exposures(self, p):
        self.p(f'resolving numbers PREMIUM AT numbers to exposures {p[0]} at {p[3]}')
        return {'exp_premium': p[0], 'exp_lr': p[3], 'exp_el': p[0] * p[3]}

    # lists for ids and numbers and builtinids ================================
    # for now, do not allow a list of severities...too tricky
    # @_('"[" builtinidl "]"')
    # def builtinids(self, p):
    #     self.p(f'resolving [builtinidl] to builtinids {p.builtinidl}')
    #     return p.builtinidl
    #
    # @_('builtinidl BUILTINID')
    # def builtinidl(self, p):
    #     s1 = f'resolving builtinidl BUILTINID {p.builtinidl}, {p.BUILTINID} --> '
    #     p.builtinidl.append(p.BUILTINID)
    #     s1 += f'{p.builtinidl}'
    #     self.p(s1)
    #     return p.builtinidl
    #
    # @_('BUILTINID')
    # def builtinidl(self, p):
    #     self.p(f'resolving BUILTINID to builtinidl {p.BUILTINID} --> {ans}')
    #     ans = [p.BUILTINID]
    #     return ans

    @_('BUILTINID')
    def builtinids(self, p):
        self.p(f'resolving BUILTINID to builtinids {p.BUILTINID}')
        return p.BUILTINID  # will always be treated as a list

    @_('"[" idl "]"')
    def ids(self, p):
        self.p(f'resolving [id1] to ids {p.idl}')
        return p.idl

    @_('idl ID')
    def idl(self, p):
        s1 = f'resolving idl ID {p.idl}, {p.ID} --> '
        p.idl.append(p.ID)
        s1 += f'{p.idl}'
        self.p(s1)
        return p.idl

    @_('ID')
    def idl(self, p):
        ans = [p.ID]
        self.p(f'resolving ID to idl {p.ID} --> {ans}')
        return ans

    @_('ID')
    def ids(self, p):
        self.p(f'resolving ID to ids {p.ID}')
        return p.ID

    @_('"[" numberl "]"')
    def numbers(self, p):
        self.p(f'resolving [number1] to numbers {p.numberl}')
        return p.numberl

    @_('numberl NUMBER')
    def numberl(self, p):
        s1 = f'resolving numberl NUMBER {p.numberl}, {p.NUMBER} --> '
        p.numberl.append(p.NUMBER)
        s1 += f'{p.numberl}'
        self.p(s1)
        return p.numberl

    @_('NUMBER')
    def numberl(self, p):
        ans = [p.NUMBER]
        self.p(f'resolving NUMBER to numberl {p.NUMBER} --> {ans}')
        return ans

    @_('NUMBER')
    def numbers(self, p):
        self.p(f'resolving NUMBER to numbers {p.NUMBER}')
        return p.NUMBER

    # elements made from named portfolios ========================
    @_('builtin_aggregate_dist TIMES NUMBER')
    def builtin_aggregate(self, p):
        """  inhomogeneous change of scale """
        self.p(f'builtin_aggregate_dist TIMES NUMBER {p.NUMBER}')
        bid = p.builtin_aggregate_dist
        bid['exp_en'] = bid.get('exp_en', 0) * p.NUMBER
        bid['exp_el'] = bid.get('exp_el', 0) * p.NUMBER
        bid['exp_premium'] = bid.get('exp_premium', 0) * p.NUMBER
        return bid

    @_('NUMBER TIMES builtin_aggregate_dist')
    def builtin_aggregate(self, p):
        """
        homogeneous change of scale

        :param p:
        :return:
        """
        self.p(f'NUMBER {p.NUMBER} TIMES builtin_aggregate_dist')
        # bid = built_in_dict, want to be careful not to add scale too much
        bid = p.builtin_aggregate_dist  # ? does this need copying. if so do in safelookup!
        if 'sev_mean' in bid:
            bid['sev_mean'] = bid['sev_mean'] * p.NUMBER
        if 'sev_scale' in bid:
            bid['sev_scale'] = bid['sev_scale'] * p.NUMBER
        if 'sev_loc' in bid:
            bid['sev_loc'] = bid['sev_loc'] * p.NUMBER
        bid['exp_attachment'] = bid.get('exp_attachment', 0) * p.NUMBER
        bid['exp_limit'] = bid.get('exp_limit', np.inf) *p.NUMBER
        bid['exp_el'] = bid.get('exp_el', 0) * p.NUMBER
        bid['exp_premium'] = bid.get('exp_premium', 0) * p.NUMBER
        return bid

    @_('builtin_aggregate_dist')
    def builtin_aggregate(self, p):
        self.p('builtin_aggregate_dist becomese builtin_aggregate')
        return p.builtin_aggregate_dist

    @_('BUILTINID')
    def builtin_aggregate_dist(self, p):
        # ensure lookup only happens here
        self.p(f'Lookup BUILTINID {p.BUILTINID}')
        built_in_dict = self._safe_lookup(p.BUILTINID, 'aggregate')
        return built_in_dict

    # ids =========================================================
    @_('SEV ID')
    def sev_name(self, p):
        self.p(f'SEV ID resolves to sev_name {p.ID}')
        return p.ID

    @_('AGG ID')
    def agg_name(self, p):
        self.p(f'AGG ID resolves to agg_name {p.ID}')
        # return {'name': p.ID}
        return p.ID

    @_('ID')
    def agg_name(self, p):
        self.p(f'ID resolves to agg_name {p.ID}')
        # return {'name': p.ID}
        return p.ID

    @_('PORT ID')
    def port_name(self, p):
        self.p(f'PORT ID resolves to port_name {p.ID}')
        # return {'name': p.ID}
        return p.ID

    def error(self, p):
        if p:
            raise ValueError(p)
        else:
            raise ValueError('Unexpected end of file')

if __name__ == '__main__':
    # print the grammar and add to this file as part of docstring
    # TODO fix comments!

    start_string = '''Language Specification
----------------------

'''
    end_string = 'parser.out parser debug information'

    with open(__file__, 'r') as f:
        txt = f.read()
    stxt = txt.split('@_')
    ans = {}
    for it in stxt[3:-1]:
        if it.find('#') >= 0:
            # skip rows with a comment between @_ and def
            pass
        else:
            b = it.split('def')
            b0 = b[0].strip()[2:-2]
            b1 = b[1].split("(self, p):")[0].strip()
            if b1 in ans:
                ans[b1] += [b0]
            else:
                ans[b1] = [b0]
    s = ''
    for k, v in ans.items():
        s += f'{k:<20s}\t:: {v[0]:<s}\n'
        for rhs in v[1:]:
            s += f'{" "*20}\t | {rhs:<s}\n'
        s += '\n'
    st = txt.find(start_string) + len(start_string)
    end = txt.find(end_string)
    txt = txt[0:st] + s + txt[end:]
    with open(__file__, 'w') as f:
        f.write(txt)
    print(s)
