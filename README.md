# PolBLiMP

Polish Benchmark of Linguistic Minimal Pairs.

Minimal pair files are available in the [polblimp/output](polblimp/output) directory.

## Quick start

Requires Python 3 with `conllu`, `pandas`, and `tqdm`.

```sh
pip install -r requirements

# Generate or regenerate morph dictionary
python polblimp/generate_morph_dict.py

# Generate files with minimal pairs
python polblimp/generate.py --paradigm all
# Files generated in ./output
```
