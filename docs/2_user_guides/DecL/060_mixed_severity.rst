.. _2_x_mixtures: 

.. reviewed 2022-12-24

Mixed Severity Distributions
-------------------------------

**Prerequisites:**  Examples use ``build`` and ``qd``, and basic :class:`Aggregate` output.


The variables in the severity clause (scale, location, distribution ID, shape
parameters, mean and CV) can be vectors to create a **mixed severity**
distribution. All elements are broadcast against one-another.

**Example**::

   sev lognorm 1000 cv [0.75 1.0 1.25 1.5 2] wts [0.4, 0.2, 0.1, 0.1, 0.1]

expresses a mixture of five lognormals, each with a mean of 1000 and CVs equal to 0.75, 1.0, 1.25, 1.5, and 2, and with weights 0.4, 0.2, 0.1, 0.1, 0.1. Equal weights are expressed
as ``wts=5``, or the relevant number of components (note equals sign). A missing weights clause is
interpreted as giving each severity weight 1 which results in five times the
total loss. Commas in the lists are optional.

.. warning::

    Weights are applied to exposure, and their meaning depends on how exposure
    is entered.

If exposure is given by claim count, then the weights apply to claim count.
This gives the usual mixture of severity curves. However, if exposure is
entered as loss or premium times a loss ratio, then the weights give the
proportion of expected loss, not the claim count. **Make sure the weights are
appropriate to the way exposure is expressed**. For example, if the mixture
is used to split small and large claims, then an 80/20 split small/large claim
counts may well correspond to a 20/80 split of expected losses (Pareto rule
of thumb).

**Example.**

This example illustrates the different behaviors of ``wts``.
The weights adjust claim counts for each mixture component when exposures are given by claims.

.. ipython:: python
    :okwarning:

    from aggregate import build, qd
    a01 = build('agg DecL:01 '
                '100 claims '
                '5000 xs 0 '
                'sev lognorm [10 20 50 75 100] '
                'cv [0.75 1.0 1.25 1.5 2] '
                'wts [0.4, 0.25, 0.15, 0.1, 0.1] '
                'poisson'
                , bs=1/2, approximation='exact')
    qd(a01)

Mixed severity with Poisson frequency is the same as the sum of five independent components. The ``report_df`` shows the mixture details.

.. ipython:: python
    :okwarning:

    qd(a01.report_df.iloc[:, :-3])

This aggregate can also be built as a :class:`Portfolio`.

.. ipython:: python
    :okwarning:

    a02 = build(
        'port DecL:02 '
            'agg Unit1 40 loss 5000 xs 0 sev lognorm 10 cv 0.75 poisson '
            'agg Unit2 25 loss 5000 xs 0 sev lognorm 20 cv 1.00 poisson '
            'agg Unit3 15 loss 5000 xs 0 sev lognorm 50 cv 1.25 poisson '
            'agg Unit4 10 loss 5000 xs 0 sev lognorm 75 cv 1.50 poisson '
            'agg Unit5 10 loss 5000 xs 0 sev lognorm 100 cv 2.00 poisson '
        , bs=1/2, approximation='exact')
    qd(a02)

Actual frequency equals total frequency times weight. Setting ``wts=5`` results in equal weights, here 0.2.

.. ipython:: python
    :okwarning:

    a03 = build('agg DecL:03 '
                '100 claims '
                '5000 xs 0 '
                'sev lognorm [10 20 50 75 100] '
                'cv [0.75 1.0 1.25 1.5 2] '
                ' wts=5 '
                'poisson'
                , bs=1/2, approximation='exact')
    qd(a03)

Missing weights are set to 1, resulting in five times loss. This behavior is generally not what you want!

.. ipython:: python
    :okwarning:

    a04 = build('agg DecL:04 '
                '100 claims '
                '5000 xs 0 '
                'sev lognorm [10 20 50 75 100] '
                'cv [0.75 1.0 1.25 1.5 2] '
                'poisson'
                , bs=1, approximation='exact')
    qd(a04)


If exposures are determined via losses (directly or using premium and loss ratio or exposure and rate), then the weights apply to expected loss. The resulting mixture is quite different.

.. ipython:: python
    :okwarning:

    a01e = build('agg DecL:01e '
                 f'{a01.agg_m} loss '
                 '5000 xs 0 '
                 'sev lognorm [10 20 50 60 70] '
                 'cv [0.75 1.0 1.25 1.5 2] '
                 'wts [0.4, 0.25, 0.15, 0.1, 0.1] '
                 'poisson'
                 , bs=1/2, approximation='exact')
    qd(a01e)
    qd(a01e.report_df.iloc[:, :-3])

.. _med example:

Mixed Exponential Distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The mixed exponential distribution (MED) is used by major US rating
bureaus to model severity and compute increased limits factors (ILFs).
This example explains how to create a MED in ``aggregate``. The
distribution is initially created as an ``Aggregate`` object with a degenerate
frequency identically equal to 1 claim to focus on the severity.
We then explain how frequency mixing interacts with a mixed severity.

The next table of exponential means and weights appears on slide 24 of `Li
Zhu, Introduction to Increased Limits Factors, 2011 RPM Basic Ratemaking
Workshop,
<https://www.casact.org/sites/default/files/presentation/rpm_2011_handouts_ws1-zhu.pdf>`_,
titled a “Sample of Actual Fitted Distribution”. At the time, it was a
reasonable curve for US commercial auto. We will use these means and
weights.


.. math::
    \small
    \begin{matrix}
    \begin{array}{@{}rr@{}}\hline
        \textbf{Mean} & \textbf{Weight}\\ \hline
        2,763      & 0.824796 \\
        24,548     & 0.159065 \\
        275,654    & 0.014444 \\
        1,917,469  & 0.001624 \\
        10,000,000 & 0.000071 \\ \hline
      \end{array}
    \end{matrix}


Here the DecL to create this mixture.

.. ipython:: python
    :okwarning:

    med = build('agg Decl:MED '
                '1 claim '
                'sev [2.764e3 24.548e3 275.654e3 1.917469e6 10e6] * '
                'expon 1 '
                'wts [0.824796 0.159065 0.014444 0.001624, 0.000071] '
                'fixed')
    qd(med)

.. note::
    Currently, it is necessary to enter a dummy shape parameter 1 for the exponential, even though it does not take a shape. This is a known bug in the parser.

The exponential distribution is surprisingly thick-tailed. It can be
regarded as the dividing line between thin and thick tailed distributions.
In order to achieve good accuracy, the modeling increases the number of
buckets to :math:`2^{18}` (i.e., ``log2=18``) and uses a bucket size ``bs=500``.
The dataframe ``report_df`` is a more detailed version of the audit dataframe
that includes information from ``statistics_df`` about each severity component.
(The reported claim counts are equal to the weights and cannot be interpreted
as fixed frequencies. They can be regarded as frequencies for a Poisson or
mixed Poisson.)

.. ipython:: python
    :okwarning:

    med.update(log2=18, bs=500)
    qd(med)

The middle diagnostic plot, the log density, shows the mixture components.

.. ipython:: python
    :okwarning:

    @savefig mixtures1.png
    med.plot()

The ``density_df`` dataframe includes a column ``lev``. From this we can pull
out ILFs. Zhu reports the ILF at 1M equals 1.52.

.. ipython:: python
    :okwarning:

    qd(med.density_df.loc[1000000, 'lev'] / med.density_df.loc[100000, 'lev'])

Here is a graph of the ILFs by limit.

.. ipython:: python
    :okwarning:

    base = med.density_df.loc[100000, 'lev']
    ax = (med.density_df.lev / base).plot(xlim=[-100000,10.1e6], ylim=[0.9, 1.85],
                                          figsize=(3.5, 2.45))
    @savefig mixtures2.png scale=20
    ax.set(xlabel='Limit', ylabel='ILF', title='Pure loss ILFs relative to 100K base');


Saving to the Knowledge
~~~~~~~~~~~~~~~~~~~~~~~~~~

We can save the MED severity in the knowledge and then refer to it by name.

.. ipython:: python
    :okwarning:

    build('sev COMMAUTO [2.764e3 24.548e3 275.654e3 1.917469e6 10e6] * '
          ' expon 1 wts [0.824796 0.159065 0.014444 0.001624, 0.000071]');

    a05 = build('agg DecL:05 [20 8 4 2] claims [1e6, 2e6 5e6 10e6] xs 0 '
                      'sev sev.COMMAUTO fixed',
                      log2=18, bs=500)

    qd(a05)

Different Distributions
~~~~~~~~~~~~~~~~~~~~~~~~~~

The kind of distribution can vary across mixtures. In the following, exposure varies
for each curve, rather than using weights, see :doc:`070_vectorization`.


.. ipython:: python
    :okwarning:

    a06 = build('agg DecL:06 [100 200] claims '
                '5000 x 0 '
                'sev [gamma lognorm] [100 150] cv [1 0.5] '
                'mixed gamma 0.5',
                log2=16, bs=2.5)
    qd(a06.report_df.iloc[:, :-2])
    @savefig mix_3.png
    a06.plot()

Using a Delaporte (shifted) gamma mixing often produces more realistic output
than a gamma, avoiding very good years.

.. ipython:: python
    :okwarning:

    a07 = build('agg DecL:07 [100 200] claims '
                 '5000 x 0 '
                 'sev [gamma lognorm] [100 150] cv [1 0.5] '
                 'mixed delaporte 0.5 0.6',
                log2=18, bs=2.5)
    qd(a07.report_df.iloc[:, :-2])
    @savefig mix_4.png
    a07.plot()



Severity Mixtures and Mixed Frequency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

All severity components in an aggregate share the same frequency mixing value,
inducing correlation between the parts. An Aon
study, :cite:t:`AonBenfield2015f`, shows that commercial auto has parameter
uncertainty CV around 25%. Building with

.. ipython:: python
    :okwarning:

    a08 = build('agg DecL:08 '
                '500 claims '
                '500000 xs 0 sev sev.COMMAUTO '
                'poisson'
                , approximation='exact')
    a09 = build('agg DecL:09 '
                '500 claims '
                '500000 xs 0 sev sev.COMMAUTO '
                'mixed gamma 0.25'
                , approximation='exact')
    qd(a08)
    qd(a09)

The effect of shared mixing is shown in ``report_df``. In order to focus on the mixing and ease the computational
burden, apply a 500,000 policy limit to model a self-insured retention.
Assume a claim count of 500 claims; for smaller portfolios the impact of mixing is less pronounced because idiosyncratic process risk dominates.

The ``independent`` column in ``report_df`` shows statitics assuming the mixture components are independent; ``mixed`` includes the effect of shared mixing variables.

The next block shows results with a Poisson frequency, where there is no mixing. The independent and mixed columns are identical.

.. ipython:: python
    :okwarning:

    qd(a08.report_df.drop(['name']).iloc[:, :-2])

This block shows mixed gamma (negative binomial) frequency. There are two differences: the individual components have higher CVs (they asymptotically approach 25% for a large portfolio), and the mixed column includes correlation between units (aggregate CV is greater than independent). Glenn Meyers had the idea of using shared mixing variables to ensure aggregate portfolio dynamics are not influenced by how the portfolio is split into units.

.. ipython:: python
    :okwarning:

    qd(a09.report_df.drop(['name']).iloc[:, :-2])


.. tidy up

.. ipython:: python
    :okwarning:
    :suppress:

    import matplotlib.pyplot as plt
    plt.close('all')
