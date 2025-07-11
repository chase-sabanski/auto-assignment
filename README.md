# auto-assignment

goals:
 1. determine which analyst should get cases based on # of occurrence
 2. distribute new cases

nit-picks:
1. I'm not crazy about the dictionary names, should have a better flow(?)

problems for future me:
I get these two warnings/caveats when my script runs.

1. See the caveats in the documentation: https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
  trimmed_input.drop([index], inplace=True)

2. auto-assignment.py:106: FutureWarning: Setting an item of incompatible dtype is deprecated and will raise an error in a future version of pandas. Value 'EMPTY' has dtype incompatible with float64, please explicitly cast to a compatible dtype first.
  input_sl_tickets.fillna("EMPTY", inplace=True)
