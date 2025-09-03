# Chainplate XML Specification (Pre‑release)

> Status: **Experimental**. Breaking changes are likely before v1.0.  
> Templates use **Jinja2** syntax (e.g., `{{ my_var }}`); variables with leading/trailing double underscores are **reserved** for the system.

---

## Overview

Chainplate defines an **XML-based markup language** for building generative‑AI workflows such as chatbots, pipelines, and agents.  
A Chainplate file consists of a single root `<pipeline>` element containing all other elements. Execution proceeds **top → bottom** and **outer → inner**.

---

## Execution Model

- **Order**: Execution is implicit and strictly **top-to-bottom, out-to-in**.  
- **Variables**: Values are stored in named variables and referenced via Jinja2, e.g., `{{ my_var_name }}`.  
- **Templating**: Any element body may contain templates; templates are resolved against the current variable context at the time of evaluation.  
- **Reserved variables**: Names that begin and end with double underscores (e.g., `__chat_output__`, `__payload__`) are **reserved**.  
- **Inputs**: The pipeline may receive input via the `--payload` CLI flag, accessible as `{{ __payload__ }}`.  
- **Conditions**: Boolean conditions use template expressions that should evaluate to `true`/`false` (or truthy/falsy).

---

## Elements

### `<pipeline>` (root)
Everything must be inside a single `<pipeline>` element.

**Attributes**
- `name` (string, **required**): A human‑readable pipeline name.

**Structure**
```xml
<pipeline name="My Pipeline">
  <!-- children -->
</pipeline>
```

---

### `<send-prompt>`
Send a prompt to the model. The element body is the prompt **content** (templated).

**Attributes**
- `output_var` (string, **required**): Name of the variable to store the model response in.

**Structure**
```xml
<send-prompt output_var="my_var_name">
  <!-- prompt content (may be a template) -->
</send-prompt>
```
**Access**: The response is available as `{{ my_var_name }}`.

---


### `<for-loop>`
Iterate a fixed number of times.

**Attributes**
- `from` (integer/string, **required**)
- `to`   (integer/string, **required**)

**Semantics**
- Iterates from `from` to `to` **inclusive**.
- Loop index is available inside the body as `{{ loop_index }}`.

**Structure**
```xml
<for-loop from="1" to="4">
  <!-- nested elements -->
</for-loop>
```

---

### `<foreach-loop>`
Iterate over a collection of items.

**Attributes**
- `input_var` (string, **required**): Name of the variable containing the collection (comma- or newline-delimited string, or list).
- `output_var` (string, **required**): Name of the variable to assign the current item to during each iteration.

**Semantics**
- Iterates over each item in the collection referenced by `input_var`.
- On each iteration, the current item is available as `{{ output_var }}` within the loop body.

**Structure**
```xml
<foreach-loop input_var="my_collection" output_var="item">
  <!-- nested elements -->
</foreach-loop>
```

**Example**
```xml
<set-variable output_var="my_collection">
  Canada, United States, Mexico, Brazil, Argentina
</set-variable>
<foreach-loop input_var="my_collection" output_var="country">
  <debug>The current country is: {{ country }}</debug>
</foreach-loop>
```

**Notes**
- The collection can be a comma-separated string, newline-separated string, or a list variable.
- Whitespace is trimmed from each item.
- The loop body is executed once for each item.
---

### `<while-loop>`
Loop while a condition remains truthy.

**Attributes**
- `condition` (template/string, **required**): Should evaluate to a boolean.

**Structure**
```xml
<while-loop condition="{{ some_boolean_expression }}">
  <!-- nested elements -->
</while-loop>
```

---

### `<set-variable>`
Assigns a value to a variable. The body is evaluated (templated) and stored.

**Attributes**
- `output_var` (string, **required**): Variable name to set.

**Structure**
```xml
<set-variable output_var="my_var_name">
  <!-- string or template -->
</set-variable>
```
**Access**: The value is available as `{{ my_var_name }}`.

---

### `<continue-if>`
Conditionally executes its body. If the condition is falsy, the body is skipped.

**Attributes**
- `condition` (template/string, **required**): Evaluates to boolean.  
- `output_var` (string, optional): If provided, the boolean result of `condition` is stored here.

**Structure**
```xml
<continue-if condition="{{ some_boolean_expression }}" output_var="my_var_name">
  <!-- nested elements executed only if condition is truthy -->
</continue-if>
```
**Access**: When `output_var` is set, the result is available as `{{ my_var_name }}`.

---

### `<interpret-as-bool>`
Parses text into a boolean and stores it.

**Attributes**
- `output_var` (string, **required**)

**Structure**
```xml
<interpret-as-bool output_var="my_bool">
  <!-- string or template -->
</interpret-as-bool>
```
**Semantics**: The body is interpreted into a boolean (implementation-defined truthy/falsy mapping).

---

### `<interpret-as-int>`
Parses text into an integer and stores it.

**Attributes**
- `output_var` (string, **required**)

**Structure**
```xml
<interpret-as-int output_var="my_int">
  <!-- string or template -->
</interpret-as-int>
```
**Semantics**: The body is parsed into an integer (error behavior is implementation-defined).

---

### `<apply-labels>`
Applies labeling criteria to an input payload and returns a comma‑delimited list of labels.

**Attributes**
- `input_var` (string, **required**): Variable name containing the input. `__payload__` is commonly used for CLI input.  
- `output_var` (string, **required**): Variable to receive the labels result (comma‑delimited string).  
- `criteria` (string, **required**): Natural‑language criteria for when to apply labels.  
- `labels` (string, optional): Comma‑delimited label set to consider.

**Structure**
```xml
<apply-labels
  input_var="__payload__"
  output_var="labels_result"
  criteria="apply any label that fits"
  labels="label_a,label_b,label_c">
  <!-- optional template/body -->
</apply-labels>
```
**Access**: The resulting labels are available as `{{ labels_result }}` (comma‑delimited string).

---

## Notes & Conventions

- **Execution order** is **top-bottom, out-in**.  
- **Reserved names**: Variables that begin and end with `__` are reserved.  
- **Templating**: Uses **Jinja2**; any valid Jinja2 expression or filter may be used where templates are supported.  
- **Variable access**: Use `{{ my_var_name }}` within templates to reference values.

---

## Minimal Example

```xml
<pipeline name="Send Prompt Example">
  <set-variable output_var="tone">Reply to everything in the silliest way possible.</set-variable>

  <send-prompt output_var="response">
    {{ tone }}
    What is the capital of France?
  </send-prompt>

  <interpret-as-bool output_var="is_long">
    {{ response | length > 80 }}
  </interpret-as-bool>

  <continue-if condition="{{ is_long }}" output_var="executed">
    <set-variable output_var="__chat_output__">{{ response }}</set-variable>
  </continue-if>
</pipeline>
```

---

## CLI Integration (context)
- The special variable `__payload__` is populated from `--payload` when invoking the CLI.  
- Final output may be surfaced by assigning `{{ ... }}` to `__chat_output__`.

---

*End of specification.*