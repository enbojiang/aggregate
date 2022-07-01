"""
=================
Underwriter Class
=================

The Underwriter is an easy to use interface into the computational functionality of aggregate.

The Underwriter
---------------

* Maintains a default library of severity curves
* Maintains a default library of aggregate distributions corresponding to industry losses in
  major classes of business, total catastrophe losses from major perils, and other useful constructs
* Maintains a default library of portfolios, including several example instances and examples used in
  papers on risk theory (e.g. the Bodoff examples)


The library functions can be listed using

::

        uw.list()

or, for more detail

::

        uw.describe()

A given example can be inspected using ``uw['cmp']`` which returns the defintion of the database
object cmp (an aggregate representing industry losses from the line Commercial Multiperil). It can
be created as an Aggregate class using ``ag = uw('cmp')``. The Aggregate class can then be updated,
plotted and various reports run on it. In iPython or Jupyter ``ag`` returns an informative HTML
description.

The real power of Underwriter is access to the agg scripting language (see parser module). The scripting
language allows severities, aggregates and portfolios to be created using more-or-less natural language.
For example

::

        pf = uw('''
        port MyCompanyBook
            agg LineA 100 claims 100000 xs 0 sev lognorm 30000 cv 1.25
            agg LineB 150 claims 250000 xs 5000 sev lognorm 50000 cv 0.9
            agg Cat 2 claims 100000000 xs 0 sev 500000 * pareto 1.8 - 500000
        ''')

creates a portfolio with three sublines, LineA, LineB and Cat. LineA is 100 (expected) claims, each pulled
from a lognormal distribution with mean of 30000 and coefficient of variation 1.25 within the layer
100000 xs 0 (i.e. limited at 100000). The frequency distribution is Poisson. LineB is similar. Cat is jsut
2 claims from the indicated limit, with severity given by a Pareto distribution with shape parameter 1.8,
scale 500000, shifted left by 500000. This corresponds to the usual Pareto with survival function
S(x) = (lambda / (lambda + x))^1.8, x >= 0.

The portfolio can be approximated using FFTs to convolve the aggregates and add the lines. The severities
are first discretized using a certain bucket-size (bs). The port object has a port.recommend_bucket() to
suggest reasonable buckets:

>> pf.recommend_bucket()

+-------+---------+--------+--------+--------+-------+-------+-------+------+------+
|       | bs10    | bs11   | bs12   | bs13   | bs14  | bs15  | bs16  | bs18 | bs20 |
+=======+=========+========+========+========+=======+=======+=======+======+======+
| LineA | 3,903   | 1,951  | 976    | 488    | 244   | 122   | 61.0  | 15.2 | 3.8  |
+-------+---------+--------+--------+--------+-------+-------+-------+------+------+
| LineB | 8,983   | 4,491  | 2,245  | 1,122  | 561   | 280   | 140   | 35.1 | 8.8  |
+-------+---------+--------+--------+--------+-------+-------+-------+------+------+
| Cat   | 97,656  | 48,828 | 24,414 | 12,207 | 6,103 | 3,051 | 1,525 | 381  | 95.4 |
+-------+---------+--------+--------+--------+-------+-------+-------+------+------+
| total | 110,543 | 55,271 | 27,635 | 13,817 | 6,908 | 3,454 | 1,727 | 431  | 108  |
+-------+---------+--------+--------+--------+-------+-------+-------+------+------+

The column bsNcorrespond to discretizing with 2**N buckets. The rows show suggested bucket sizes for each
line and in total. For example with N=13 (i.e. 8196 buckets) the suggestion is 13817. It is best the bucket
size is a divisor of any limits or attachment points, so we select 10000.

Updating can then be run as

::

    bs = 10000
    pf.update(13, bs)
    pf.report('quick')
    pf.plot('density')
    pf.plot('density', logy=True)
    print(pf)

    Portfolio name           MyCompanyBook
    Theoretic expected loss     10,684,541.2
    Actual expected loss        10,657,381.1
    Error                          -0.002542
    Discretization size                   13
    Bucket size                     10000.00
    <aggregate.port.Portfolio object at 0x0000023950683CF8>


Etc. etc.

"""

import numpy as np
import logging
import pandas as pd
from pathlib import Path
from inspect import signature
from pprint import PrettyPrinter

from .port import Portfolio
from .distr import Aggregate, Severity
from .parser import UnderwritingLexer, UnderwritingParser

logger = logging.getLogger(__name__)


class Underwriter(object):
    """
    The ``Underwriter`` class manages the creation of Aggregate and Portfolio objects, and
    maintains a database of standard Severity (curves) and Aggregate (unit or line level) objects.
    The ``Underwriter`` knows about all the business that is written!

    * Handles persistence to and from agg files
    * Is interface into program parser
    * Handles safe lookup from database for parser

    """

    data_types = ['port', 'agg', 'sev']

    def __init__(self, name='Rory', databases=None, glob=None, store_mode=True, update=False,
                 log2=10, debug=False, create_all=False):
        """

        :param dir_name:
        :param name:
        :param databases: if None: nothing loaded; if 'default' or 'default' in databases load the installed
        databases; if 'site' or site in databases, load all site databases (home() / agg, which
        is created it it does not exist); other entires treated as db names in home() / agg are then loaded.
        Databases not in site directory must be fully qualified path names.
        :param glob: reference, e.g. to globals(), used to resolve meta.XX references
        :param store_mode: add newly created aggregates to the uw knowledge?
        :param update:
        :param log2:
        :param debug: run parser in debug mode
        :param create_all: by default write only creates portfolios.
        """

        self.last_spec = None
        self.name = name
        self.update = update
        if log2 <= 0:
            raise ValueError('log2 must be > 0. The number of buckets used equals 2**log2.')
        self.log2 = log2
        self.debug = debug
        self.glob = glob
        self.lexer = UnderwritingLexer()
        self.parser = UnderwritingParser(self._safe_lookup, debug)
        # stop pyCharm complaining
        # knowledge - accounts and line known to the underwriter
        self._knowledge = {}
        # self.severity = {}
        # self.aggregate = {}
        # self.portfolio = {}

        if databases == 'all':
            databases = ['default', 'site']
        elif type(databases) == str:
            databases = [databases]
        default_dir = Path(__file__).parent / 'agg'
        site_dir = Path.home() / 'aggregate'

        # TODO Useful?
        self.dir_name = site_dir
        if self.dir_name.exists() is False:
            # check site dir exists
            self.dir_name.mkdir(parents=True, exist_ok=True)

        # make sure all database entries are stored:
        self.store_mode = True
        if databases is None:
            # nothing to do
            databases = []

        if 'default' in databases:
            databases.remove('default')
            for fn in default_dir.glob('*.agg'):
                self._read_db(fn)

        if 'site' in databases:
            databases.remove('site')
            databases += list(site_dir.glob('*.agg'))

        for fn in databases:
            if Path(fn).exists():
                self._read_db(fn)
            elif (site_dir / fn).exists():
                self._read_db(site_dir / fn)
            else:
                logger.warning(f'Database {fn} not found. Ignoring.')

        # set desired store_mode
        self.store_mode = store_mode
        self.create_all = create_all

    def _read_db(self, db_path):
        if not isinstance(db_path, Path):
            db_path = Path(db_path)
        try:
            program = db_path.read_test(encoding='utf-8')
        except FileNotFoundError:
            logger.warning(f'Requested database {db_path.name} not found. Ignoring.')
        # read in, parse, save to sev/agg/port dictionaries
        self.interpret_program(program)

    def __getitem__(self, item):
        """
        handles self[item]

        subscriptable: try user portfolios, b/in portfolios, line, severity
        to access specifically use severity or line methods

        :param item:
        :return:
        """
        # much less fancy version:
        for kind in self.data_types:
            obj = self._knowledge.get((kind, item), None)
            if obj is not None:
                logger.debug(f'Underwriter.__getitem__ | found {item} of type {kind}')
                return kind, obj
        raise LookupError(f'Item {item} not found in any database')

    def _repr_html_(self):
        s = [f'<h1>Underwriter Knowledge</h1>',
             f'Underwriter {self.name} has knowledge of {len(self._knowledge)} portfolios, '
             f'aggregate units, and severities:<br>']
        s.append(', '.join([f'{n} ({k})' for (k, n), v in
                            sorted(self._knowledge.items())]))
        s.append(f'<h3>Settings</h3>')
        for k in ['name', 'update', 'log2', 'store_mode', 'last_spec', 'create_all']:
            s.append(f'<span style="color: red;">{k}</span>: {getattr(self, k)}; ')
        return '\n'.join(s)

    def __call__(self, portfolio_program, **kwargs):
        """
        make the Underwriter object callable; pass through to write

        :param portfolio_program:
        :return:
        """
        return self.write(portfolio_program, **kwargs)

    @property
    def knowledge(self):
        """
        Return the knowledge as a nice dataframe

        :return:
        """
        df = pd.DataFrame(self._knowledge.values(),
                          columns=['program'],
                          index=pd.MultiIndex.from_tuples(self._knowledge.keys(),
                                                          names=['kind', 'name']))
        return df

    def list(self):
        """
        list all available databases

        :return:
        """
        sers = dict()
        for k in Underwriter.data_types:
            # d = sorted(list(self.__getattribute__(k).keys()))
            d = sorted(list(getattr(self, k).keys()))
            sers[k.title()] = pd.Series(d, index=range(len(d)), name=k)
        df = pd.DataFrame(data=sers)
        df = df.fillna('')
        return df

    def describe(self, item_types=''):
        """
        More informative version of list including notes.

        TODO: enhance!

        :return:
        """

        cols = ['Name', 'Type', 'Severity', 'ESev', 'Sev_a', 'Sev_b', 'EN', 'Freq_a', 'ELoss', 'Notes']
        # what they are actually called
        cols_agg = ['sev_name', 'sev_mean', 'sev_a', 'sev_b', 'exp_en', 'freq_a', 'exp_el', 'note']
        defaults = ['', 0, 0, 0, 0, 0, 0, '']
        df = pd.DataFrame(columns=cols)
        df = df.set_index('Name')

        if item_types == '':
            # all item types
            item_types = Underwriter.data_types
        else:
            item_types = [item_types.lower()]

        for item_type in item_types:
            for obj_name, obj_values in getattr(self, item_type).items():
                data_fields = [obj_values.get(c, d) for c, d in zip(cols_agg, defaults)]
                df.loc[obj_name, :] = [item_type] + data_fields

        df = df.fillna('')
        return df

    def parse_portfolio_program(self, portfolio_program, output='spec'):
        """
        Utility routine to parse the program and return the spec suitable to pass to Portfolio to
        create the object.
        Initially just for a single portfolio program (which it checks!)
        No argument of default conniptions

        To write program in testing mode use output='df':

        * dictionary definitions are added to uw but no objects are created
        * returns data frame description of added severity/aggregate/portfolios
        * the dataframe of aggregates can be used to create a portfolio (with all the aggregates) by calling

        ```Portfolio.from_DataFrame(name df)```

        To parse and get dictionary definitions use output='spec'.
        Aggregate and severity objects are also returned though they could be
        accessed directly using wu['name']. May be convenient...we'll see.

        Output has form that an Aggregate can be created from Aggregate(**x['name'])
        etc. which is a bit easier than uw['name'] which returns the type.

        TODO make more robust

        :param portfolio_program:
        :param output:  'spec' output a spec (assumes only one portfolio),
                        or a dictionary {name: spec_list} if multiple
                        'df' or 'dataframe' output as pandas data frame
                        'dict' output as dictionary of pandas data frames (old write_test output)
        :return:
        """

        self.interpret_program(portfolio_program)

        # if globs replace all meta objects with a lookup object
        # copy from code below FRAGILE
        if self.glob is not None:
            for a in list(self.parser.agg_out_dict.values()) + list(self.parser.sev_out_dict.values()):
                if a['sev_name'][0:4] == 'meta':
                    obj_name = a['sev_name'][5:]
                    try:
                        obj = self.glob[obj_name]
                    except NameError as e:
                        print(f'Object {obj_name} passed as a proto-severity cannot be found')
                        raise e
                    a['sev_name'] = obj
                    logger.debug(f'Underwriter.write | {a["sev_name"]} ({type(a)} reference to {obj_name} '
                                 f'replaced with object {obj.name} from glob')

        if output == 'spec':
            # expecting a single portfolio for this simple function
            # create the spec list string
            if len(self.parser.port_out_dict) == 1:
                # this behaviour to ensure backwards compatibility
                nm = ""
                spec_list = None
                for nm in self.parser.port_out_dict.keys():
                    # remember the spec comes back as a list of aggs that have been entered into the uw
                    # self[v] = ('agg', dictionary def) of the agg component v of the portfolio
                    spec_list = [self[v][1] for v in self.portfolio[nm]['spec']]
                return nm, spec_list

            elif len(self.parser.port_out_dict) > 1 or \
                    len(self.parser.agg_out_dict) or len(self.parser.sev_out_dict):
                # return dictionary: {pf_name : { name: pf_name, spec_list : [list] }}
                # so that you can call Portfolio(*output[pf_name]) to create pf_name
                # notes are dropped...
                ans = {}
                for nm in self.parser.port_out_dict.keys():
                    # remember the spec comes back as a list of aggs that have been entered into the uw
                    # self[v] = ('agg', dictionary def) of the agg component v of the portfolio
                    spec_list = [self[v][1] for v in self.portfolio[nm]['spec']]
                    ans[nm] = dict(name=nm, spec_list=spec_list)

                for nm in self.parser.agg_out_dict.keys():
                    ans[nm] = self.aggregate[nm]

                for nm in self.parser.sev_out_dict.keys():
                    ans[nm] = self.severity[nm]

                return ans

            else:
                logger.warning(f'Underwriter.parse_portfolio_program | program has no Portfolio outputs. '
                               'Nothing returned. ')
                return

        elif output == 'df' or output.lower() == 'dataframe':
            logger.debug(f'Runner.write_test | Executing program\n{portfolio_program[:500]}\n\n')
            ans = {}
            if len(self.parser.sev_out_dict) > 0:
                for v in self.parser.sev_out_dict.values():
                    Underwriter.add_defaults(v, 'sev')
                ans['sev'] = pd.DataFrame(list(self.parser.sev_out_dict.values()),
                                          index=self.parser.sev_out_dict.keys())
            if len(self.parser.agg_out_dict) > 0:
                for v in self.parser.agg_out_dict.values():
                    Underwriter.add_defaults(v)
                ans['agg'] = pd.DataFrame(list(self.parser.agg_out_dict.values()),
                                          index=self.parser.agg_out_dict.keys())
            if len(self.parser.port_out_dict) > 0:
                ans['port'] = pd.DataFrame(list(self.parser.port_out_dict.values()),
                                           index=self.parser.port_out_dict.keys())
            return ans

        else:
            raise ValueError(f'Inadmissible output type {output}  passed to parse_portfolio_program. '
                             'Expecting spec or df/dataframe.')

    def write(self, portfolio_program, log2=0, bs=0, **kwargs):
        """
        Write a natural language program. Write carries out the following steps.

        1. Read in the program and cleans it (e.g. punctuation, parens etc. are
        removed and ignored, replace ; with new line etc.)
        2. Parse line by line to create a dictioonary definition of sev, agg or port objects
        3. If glob set, pull in objects
        4. replace sev.name, agg.name and port.name references with their objects
        5. If create_all set, create all objects and return in dictionary. If not set only create the port objects
        6. If update set, update all created objects.

        Sample input

        ::

            port MY_PORTFOLIO
                agg Line1 20  loss 3 x 2 sev gamma 5 cv 0.30 mixed gamma 0.4
                agg Line2 10  claims 3 x 2 sevgamma 12 cv 0.30 mixed gamma 1.2
                agg Line 3100  premium at 0.4 3 x 2 sev 4 @ lognormal 3 cv 0.8 fixed 1

        The indents are required...

        See parser for full language spec! See Aggregate class for many examples.

        Reasonable kwargs:

        * bs
        * log2
        * update overrides class default
        * add_exa should port.add_exa add the exa related columns to the output?
        * create_all: create all objects, default just portfolios. You generally
                     don't want to create underlying sevs and aggs in a portfolio.

        :param portfolio_program:
        :param kwargs:
        :return: single created object or dictionary name: object
        """

        # prepare for update
        # what / how to do; little awkward: to make easier for user have to strip named update args
        # out of kwargs
        if 'create_all' in kwargs:
            create_all = kwargs['create_all']
            del kwargs['create_all']
        else:
            create_all = self.create_all

        if 'update' in kwargs:
            update = kwargs['update']
            del kwargs['update']
        else:
            update = self.update

        if update is True and log2 == 0:
            log2 = self.log2

        # first see if portfolio_program refers to a built-in object
        kind = ''
        obj = None
        try:
            kind, obj = self.__getitem__(portfolio_program)
        except LookupError:
            logger.debug(f'underwriter.write | object not found, will process as program')
        else:
            logger.debug(f'underwriter.write | object found, returning object')
            if kind == 'agg':
                obj = Aggregate(**obj)
                if update:
                    obj.easy_update(log2, bs)
                return obj
            elif kind == 'port':
                # actually make the object
                obj = Portfolio(portfolio_program, [self[v][1] for v in obj['spec']])
                if update is True:
                    obj.update(log2=log2, bs=bs, **kwargs)
                    logger.debug(f"Underwriter.write | updating Portfolio {portfolio_program} log2={log2}, bs={bs}")
                return obj
            elif kind == 'sev':
                if 'sev_wt' in obj:
                    del obj['sev_wt']
                return Severity(**obj)
            else:
                ValueError(f'Cannot build {kind} objects')
            print('NEVER GET HERE??? ' * 10)
            return obj

        # if you fall through to here then the portfolio_program did not refer to a built in object
        # run the program
        self.interpret_program(portfolio_program)

        # if globs, replace all meta objects with a lookup object
        if self.glob is not None:
            logger.debug(f'Underwriter.write | Resolving globals')
            for (k, n), v in self.parser.out_dict.items():
                if k in ['sev', 'agg']:
                    if v['sev_name'][0:4] == 'meta':
                        logger.debug(f'Underwriter.write | Resolving {v["sev_name"]}')
                        obj_name = v['sev_name'][5:]
                        try:
                            obj = self.glob[obj_name]
                        except NameError as e:
                            print(f'Object {obj_name} passed as a meta object cannot be found in glob.')
                            raise e
                        v['sev_name'] = obj
                        logger.debug(f'Underwriter.write | {v["sev_name"]} ({k} reference to {obj_name} '
                                     f'replaced with object {obj.name} from glob.')
            logger.debug(f'Underwriter.write | Done resolving globals')

        # create objects
        # 2019-11: create all objects not just the portfolios if create_all==True
        # rv = return values
        rv = None
        if len(self.parser.out_dict) > 0:
            # create ports
            rv = {}
            # parser.out_dict is indexed by (kind, name) and contains the defining dictionary
            # PrettyPrinter().pprint(self.parser.out_dict)
            for (kind, name), v in self. parser.out_dict.items():
                # remember the spec comes back as a list of aggs that have been entered into the uw
                if kind == 'port':
                    obj = Portfolio(name, v) #  [self[v][1] for v in self.portfolio[k]['spec']])
                    if update is True:
                        obj.update(log2=log2, bs=bs, **kwargs)
                        logger.debug(f"Underwriter.write | updating Portfolio {obj.name} log2={log2}, bs={bs}")
                    rv[(kind, name)] = obj
                elif kind == 'agg':
                    if create_all is True:
                        if rv is None:
                            rv = {}
                        obj = Aggregate(**v)  # k, **{kk: vv for kk, vv in v.items() if kk != 'name'})
                        if update:
                            obj.easy_update(log2)
                        rv[(kind, name)] = obj
                elif kind == 'sev':
                    if create_all is True:
                        if rv is None:
                            rv = {}
                        # this gets added by the parser but is not wanted! 
                        if 'sev_wt' in v:
                            del v['sev_wt']
                        obj = Severity(**v)  # k, **{kk: vv for kk, vv in v.items() if kk != 'name'})
                        rv[(kind, name)] = obj

        # report on what has been done
        if rv is None:
            # print('WARNING: Program did not contain any output...')
            logger.warning(f'Underwriter.write | Program did not contain any output')
        else:
            if len(rv):
                logger.info(f'Underwriter.write | Program created {len(rv)} objects.')
            if len(rv) == 1:
                # dict, pop the last (only) element
                rv = rv.popitem()[1]

        # return created objects
        return rv

    def write_from_file(self, file_name, log2=0, bs=0, update=False, **kwargs):
        """
        read program from file. delegates to write

        :param file_name:
        :param log2:
        :param bs:
        :param update:
        :param kwargs:
        :return:
        """
        portfolio_program = Path(file_name).read_text(encoding='utf-8')
        return self.write(portfolio_program, log2=log2, bs=bs, update=update, **kwargs)

    def interpret_program(self, portfolio_program):
        """
        Preprocess and then parse one line at a time.

        Error handling through parser.

        Old parse_portfolio_program replaced with build.interpret_one and interpret_test,
        and running write with

        :param portfolio_program:
        :return:
        """

        # Preprocess ---------------------------------------------------------------------
        portfolio_program = UnderwritingLexer.preprocess(portfolio_program)

        # Parse and Postprocess-----------------------------------------------------------
        rv = {}
        self.parser.reset()
        for program_line in portfolio_program:
            logger.debug(program_line)
            # preprocessor only returns lines of length > 0
            try:
                # parser returns the type and name of the object
                kind, name = self.parser.parse(self.lexer.tokenize(program_line))
            except ValueError as e:
                if isinstance(e.args[0], str):
                    logger.error(e)
                    raise e
                else:
                    t = e.args[0].type
                    v = e.args[0].value
                    i = e.args[0].index
                    txt2 = program_line[0:i] + f'>>>' + program_line[i:]
                    logger.error(f'Parse error in input "{txt2}"\nValue {v} of type {t} not expected')
                    raise e
            else:
                logger.info(f'{kind} object {name} parsed successfully' +
                            (f', adding to uw object' if self.store_mode else
                             f', adding to rv'))
                # if in store_mode, add the program to uw dictionaries
                if self.store_mode:
                    self._knowledge[(kind, name)] = program_line
                else:
                    rv[name] = (kind, self.parser.out_dict[(kind, name)])
        return rv

    @staticmethod
    def add_defaults(dict_in, kind='agg'):
        """
        add default values to dict_inin. Leave existing values unchanged
        Used to output to a data frame, where you want all columns completed

        :param dict_in:
        :param kind:
        :return:
        """

        print('running add_defaults\n' * 10)

        # use inspect to get the defaults
        # obtain signature
        sig = signature(Aggregate.__init__)

        # self and name --> bound signature
        bs = sig.bind(None, '')
        bs.apply_defaults()
        # remove self
        bs.arguments.pop('self')
        defaults = bs.arguments

        if kind == 'agg':
            defaults.update(dict_in)

        elif kind == 'sev':
            for k, v in defaults.items():
                if k[0:3] == 'sev' and k not in dict_in and k != 'sev_wt':
                    dict_in[k] = v

    def _safe_lookup(self, full_uw_id):
        """
        lookup uw_id in uw of expected type and merge safely into self.arg_dict
        delete name and note if appropriate

        :param full_uw_id:  type.name format
        :return:
        """

        expected_type, uw_id = full_uw_id.split('.')
        try:
            # lookup in Underwriter
            found_type, found_dict = self[uw_id]
        except LookupError as e:
            logger.error(f'ERROR id {expected_type}.{uw_id} not found')
            raise e
        logger.debug(f'UnderwritingParser._safe_lookup | retrieved {uw_id} as type {found_type}')
        if found_type != expected_type:
            raise ValueError(f'Error: type of {uw_id} is  {found_type}, not expected {expected_type}')
        return found_dict.copy()


def safelookup(val):
    """ for debugging """
    s = f'LOOKUP {val}'
    return {'sev_name': 'BUILTIN', 'sev_a': val}



class Build(object):
    uw = Underwriter(create_all=True)

    @classmethod
    def parse(cls, program):
        return cls.uw.parse_portfolio_program(program)

    @classmethod
    def list(cls):
        return cls.uw.list()

    @classmethod
    def describe(cls, item_type=''):
        return cls.uw.describe(item_type, pretty_print=True)

    @classmethod
    def build(cls, program, update=True, bs=0, log2=13, padding=1, **kwargs):
        """
        Convenience function to make work easy for the user. Hide uw, updating etc.

        :param program:
        :param bs:
        :param log2:
        :param padding:
        :param kwargs: passed to update
        :return:
        """
        # tamper down the logging
        logger.setLevel(30)

        if program in ['underwriter', 'uw']:
            return cls.uw

        # make stuff
        out = cls.uw(program)

        if isinstance(out, dict):
            pass
        elif isinstance(out, Aggregate) and update is True:
            d = out.spec
            if d['sev_name'] == 'dhistogram':
                bs = 1
                # how big?
                if d['freq_name'] == 'fixed':
                    max_loss = np.max(d['sev_xs']) * d['exp_en']
                else:
                    max_loss = np.max(d['sev_xs']) * d['exp_en'] * 2
                # bins are 0b111
                log2 = len(bin(int(max_loss))) - 1
                logger.info(f'Discrete input, using bs=1 and log2={log2}')
            out.easy_update(log2=log2, bs=bs, padding=padding, **kwargs)
        elif isinstance(out, Severity):
            # there is no updating for severities
            pass

        else:
            pass

        return out

    __call__ = build

    @staticmethod
    def interpreter_test(where='', filename='C:\\S\\TELOS\\Python\\aggregate_extensions_project\\aggregate2\\agg2_database.csv'):
        """
        Run a suite of test programs. For detailed analysis, run_one.

        """
        df = pd.read_csv(filename, index_col=0)
        if where != '':
            df = df.loc[df.index.str.match(where)]

        lexer = UnderwritingLexer()
        parser = UnderwritingParser(safelookup, False)
        ans = {}
        errs = 0
        no_errs = 0
        # detect non-trivial change
        f = lambda x, y: '' if x.replace(' ', '') == y.replace(' ', '').replace('\t', '') else y
        for k, v in df.iterrows():
            parser.reset()
            v_in = v[0]
            v = lexer.preprocess(v_in)
            if len(v) == 1:
                v = v[0]
                try:
                    kind, obj = parser.parse(lexer.tokenize(v))
                except (ValueError, TypeError) as e:
                    kind = 'error'
                    obj = str(e)
                    errs += 1
                else:
                    no_errs += 1
                ans[k] = [kind, obj, v, f(v, v_in)]
            elif len(v) > 1:
                logger.info(f'{v_in} preprocesses to {len(v)} lines; not processing.')
                ans[k] = ['multiline', None, v, v_in]
            else:
                logger.info(f'{v_in} preprocesses to a blank line; ignoring.')
                ans[k] = ['blank', None, v, v_in]

        print((f'No errors reported.\n' if errs == 0 else f'{errs} errors reported.\n') +
              f'{no_errs} programs parsed successfully.')
        df_out = pd.DataFrame(ans, index=['type', 'name', 'program', 'raw_input']).T
        display(df_out)
        return df_out, errs, ans

    @staticmethod
    def interpret_one(v):
        """
        Interpret single test in debug mode.
        """
        lexer = UnderwritingLexer()
        parser = UnderwritingParser(safelookup, True)
        print(f'Interpret one test\n{v}')
        print('='*len(v))
        v1 = lexer.preprocess(v)
        if len(v1) > 1:
            logger.error('Input program contains more than one entry. Only interpreting the first...interpret_**one**')
        v1 = v1[0]
        if v1 != v:
            print(f'Preprocessed input:\n{v1}')
        parser.reset()
        try:
            kind, name = parser.parse(lexer.tokenize(v1))
        except ValueError as e:
            print('!!!!!!! Value Error !!!!!!!' * 4)
            raise e

        pp = PrettyPrinter().pprint
        print(f'\nFound {kind} object {name}')
        pp(parser.out_dict[(kind, name)])


# exported item
build = Build()
