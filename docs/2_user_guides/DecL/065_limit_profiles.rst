.. reviewed 2022-12-24

Limit Profiles
------------------

**Prerequisites:**  Examples use ``build`` and ``qd``, and basic :class:`Aggregate` output.

All exposure variables can be vectors. This feature makes it easy to express a **limit profile**. All exposure
related elements (claim count, premium, loss, loss ratio) are broadcast against
one-another.

**Example**::

   agg Eg1                                  \
   [1000 2000 4000 1000] premium at 0.65 lr \
   [1000 2000 5000 4000] xs [0 0 0 1000]    \
   sev lognorm 500 cv 1.25                  \
   mixed gamma 0.6

expresses a limit profile with 1000 of premium at 1000 xs 0; 2000 at 2000
xs 0, 4000 at 5000 xs 0, and 1000 at 4000 xs 1000. In this case all the loss
ratios are the same, but they could vary too.

A (mixed) compound Poisson aggregate with a mixed severity is a sum of aggregates,
with the mixture weights applied to the expected claim count. This is
analogous to the fact that :math:`\exp(a+b)=\exp(a)\exp(b)`. In terms of
a compound Poisson,

.. math:: \mathsf{CP}(\lambda, \sum w_iF_i)=_d \sum_i \mathsf{CP}(w_i \lambda, F_i)

where :math:`=_d` indcates the two sides have the same distribution. For Poisson frequency, the components on the right are independent; for mixed frequencies they are not.

In this case, we have selected a mixed frequency, using a gamma CV 0.6
mixing distribution. All of the limits share the same mixing variable.
The effect of this is shown in the ``report_df``, comparing the independent
and mixed columns. The former adds the mixture components independently
whereas the latter uses the common mixing variable. The increase in
aggregate CV is quite marked.

.. ipython:: python
    :okwarning:

    from aggregate import build, qd
    a10 = build('agg DecL:10 '
                '[1000 2000 4000 1000] premium at 0.65 lr '
                '[1000 2000 5000 4000] xs [0 0 0 1000] '
                'sev lognorm 500 cv 1.25 '
                'mixed gamma 0.6')
    qd(a10)
    qd(a10.report_df.iloc[:, :-2])


.. tidy up

.. ipython:: python
    :suppress:

    import matplotlib.pyplot as plt
    plt.close('all')
