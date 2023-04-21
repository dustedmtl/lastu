## Samples

For all of the input file formats the following is true:
 - The file type is determined by the first line with the format `# type = <type>`
   - `<type` can be either `form`, `lemma` or `nonword`
  - For this line, all whitespace is ignored, that is, the tokens `type`, `=` and `<type>` can be separated by zero or more space characters.
    - See the examples below.
 - All other comment lines (that start with the character `#`) are ignored


### Form input file:
```
# type=form
# Only process surface forms
kuusi
auto
näätä
```

### Lemma input file:
```
# type = lemma
# Only process lemmas
kuusi
voida
voi
autotalli
```

### Non-word input file:
```
# type =nonword
# Only process nonwords
babalapa
auti
sautk
fääfä
```
