.. _design and purpose:

.. reviewed 2022-12-24

DecL Design and Purpose
------------------------

The Dec Language, or simply DecL, is designed to make it easy to go from "Dec page to distribution" --- hence the name. An insurance policy's Declarations page spells out key coverage terms and conditions such as the limit and deductible, effective date, named insured, and covered property. A reinsurance slip performs the same functions.

Coverage expressed concisely in words on a Dec page is often incomplete and hard to program. Consider the declaration

    "Aggregate losses from trucking policy with a premium of 2000, a limit of 1000, and no deductible."

To estimate the distribution of outcomes for this policy, the actuary must:

#. Estimate the priced loss ratio on the policy to determine the loss pick (expected loss) as premium times loss ratio. Say they select 67.5%.
#. Select a suitable trucking ground-up severity curve, say lognormal with mean 100 and CV 1.75.
#. Compute the expected conditional layer severity for the layer 1000 xs 0.
#. Divide severity into the loss pick to determine the expected claim count.
#. Select a suitable frequency distribution, say Poisson.
#. Calculate a numerical approximation to the resulting compound-Poisson aggregate distribution

A DecL program takes care of many of these details. The DecL program corresponding to the trucking policy is simply::

    agg Trucking                      \
        2000 premium at 0.675 lr      \
        1000 xs 0                     \
        sev lognorm 100 cv 1.75       \
        poisson

It specifies the loss ratio and distributions selected in steps 1, 2 and 5; these require actuarial judgment and cannot be automated. Based on this input, the ``aggregate`` package computes the rest of steps 1, 3, 4, and 6. The details of the program are explained in the rest of this chapter.

.. note::
    All DecL programs are one-line long. The program above uses a Python ``\`` line break so that the code above can be cut and pasted as an argument to ``build`` using a triple quoted string. See :ref:`10 mins formatting`.

Specifying a Realistic Aggregate Distribution
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The trucking example hints at the complexity of specifying a realistic insurance aggregate distribution. Abstracting the details, a complete specification has seven parts:

1. A name
2. The exposure, optionally including occurrence limits and deductibles
3. The ground-up severity distribution
4. Occurrence reinsurance (optional)
5. The frequency distribution
6. Aggregate reinsurance (optional)
7. Additional notes (optional)

DecL follows the same pattern::

    agg name                   \
        exposure <limit>       \
        severity               \
        <occurrence re>        \
        <frequency>            \
        <aggregate re>         \
        <note>

where ``<...>`` denotes an optional clause. All programs are one-line long and horizontal white space is ignored.

DecL programs are built (interpreted) using the ``build`` function. Python automatically concatenates strings between parenthesis (no need for ``\``), making it is easiest and clearest to enter a program as::

    build('agg Trucking '
          '2000 premium at 0.675 lr '
          '1000 xs 0 '
          'sev lognorm 100 cv 1.75 '
          'poisson')

The entries in this example are as follows.


* ``agg`` is the DecL keyword used to create an aggregate distribution. Keywords are part of the language, like ``if/then/else`` in VBA, R or Python, or ``select`` in SQL.

* ``Trucking`` is a string name. It can contain letters and numbers and periods and must start with a letter. It is case sensitive. It cannot contain an underscore. It cannot be a DecL keyword. E.g., ``Motor``, ``NE.Region``, ``Unit.A`` but not ``12Line`` or ``NE_Region``.

* The exposure clause is ``2000 premium at 0.675 lr 1000 xs 0``. (Percent notation is acceptable: the loss ratio can be entered as ``67.5% lr``.) It determines the volume of insurance, see :doc:`020_exposure`. It includes ``1000 xs 0``, an optional :ref:`layers subclause<2_agg_class_layers_subclause>` to set policy occurrence limits and deductibles.

* The severity clause ``sev lognorm 100 cv 1.75`` determines the **ground-up** severity, see :ref:`severity <2_agg_class_severity_clause>`. ``sev`` is a keyword


* The ``frequency`` clause, ``poisson``, specifies the frequency distribution, see :ref:`frequency <2_agg_class_frequency_clause>`.

The occurrence re, aggregate re and note clauses are omitted. See :ref:`2_agg_class_reinsurance_clause` and :doc:`090_notes`.

``aggregate`` automatically computes the expected claim count from the premium, expected loss ratio, and average severity.

Python ``f``-strings allow variables to be passed into DecL programs, ``f'sev lognorm {x} cv {cv}``.

Alternative Specifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are two other specifications for different situations that reference a
distribution from the ``knowledge`` database.

The first simply refers to the object by name, prefixing it with ``agg.``. Thus::

    agg.Trucking

refers to the ``Trucking`` example above.

The second allows the flexibility to provide a new name for the object::

    agg NewTruckingAccount agg.Trucking

These forms are mostly used in portfolios.
See the :doc:`../../4_dec_Language_Reference`.

The rest of this Chapter describes the basic features of each clause.
