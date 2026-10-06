# Input Data Format

This document describes the required structure for the input files used in this multiway number partitioning solver.

## Structure

The input file must be a plain text file formatted according to the following rules:

1. First Line: A single integer representing the total number of datasets contained in the file.
2. Subsequent Lines: Each subsequent line represents exactly one dataset.
    - The integers within a single dataset must be separated by a space.
    - Each individual dataset must be separated by a newline (i.e., every dataset gets its own line).

## Example Input

Here is an example of a valid input file containing 3 distinct datasets:

```
3
4 5 6 7 8 4 3 2 8 9 12 11
10 20 30 40 50
1 1 1 1 1 1 1 1 1 1
```