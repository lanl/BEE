"""Code for CWL expressions."""

import re


def eval_output(input_pairs, glob):
    """Evaluate a simple output expression."""
    # Find all matches of string pattern $(inputs.foo), capturing value of foo
    expr_pattern = r"\$\(inputs\.(\w+)\)"
    match = re.findall(expr_pattern, glob)
    if match:
        # Split string up to get list of non-matching characters
        split_pattern = r"\$\(inputs\.\w+\)"
        split = re.split(split_pattern, glob)
        values = []
        for m in match:
            print(m)
            if m in input_pairs.keys():
                values.append(input_pairs[m])
            else:
                raise ValueError(f"reference to non-existent task input {m}")
        # Construct string with evaluated inputs
        eval_string = split[0]
        for v, s in zip(values, split[1:]):
            eval_string += v + s
        return eval_string
    raise RuntimeError(f'could not parse output expression in glob: {glob}')


def eval_input(input_pairs, value_from):
    """Evaluate a simple input expression."""
    # Match any of the following patterns: self.path, inputs.foo, or "foo"
    # in an expression of the form $(A + B) in the valueFrom field
    expr_pattern = r'\$\((self\.path|inputs\.\w+|".+") \+ (self\.path|inputs\.\w+|".+")\)'
    match = re.fullmatch(expr_pattern, value_from)
    if match:
        values = []
        for m in match.groups():
            inputs_dot = "inputs."
            if m == "self.path":
                raise NotImplementedError('Using "self.path" in a "value_from" field '
                                          'is not yet supported')
            if m.startswith(inputs_dot):
                if m[len(inputs_dot):] in input_pairs.keys():
                    values.append(input_pairs[m[len(inputs_dot):]])
                else:
                    raise ValueError(f"reference to non-existent task input {m[len(inputs_dot):]}")
            else:
                # Pattern "foo" (strip quotes)
                values.append(m[1:-1])
        return values[0] + values[1]
    raise ValueError(f"unable to evaluate expression {value_from}")
