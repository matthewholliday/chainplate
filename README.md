
# Chainplate: AI Workflow Markup Language

AIXML is an XML-based language for interacting with AI models, allowing users to define structured prompts and workflows. It is designed for rapid prototyping of AI flows and agents, providing a flexible way to orchestrate LLM calls, variable management, and conditional logic in a readable XML format.

> **Note:** AIXML is in pre-release and under active development. APIs and features may change.

## Features

- **XML-based syntax** for defining AI workflows
- **Core library** for parsing and executing AIXML documents
- **Command-line interface (CLI)** for processing AIXML files
- **Rapid prototyping** of AI agents and flows

## Example Syntax

```xml
<pipeline name="Example Pipeline">
	<set-variable output_var="user_input">Hello world!</set-variable>
	<interpret-as-bool input_var="user_input" output_var="is_greeting" />
	<continue-if condition="{{ is_greeting }}">
		<debug>The input was a greeting.</debug>
	</continue-if>
	<write-to-file filename="output.txt">
		Result: {{ is_greeting }}
	</write-to-file>
</pipeline>
```

## CLI Usage

The CLI is invoked as `aixml` and supports several commands and options:

### Parse XML to JSON

```
python -m aixml --parse-to-json -i input.xml -o output.json
```
- Parses the input XML and outputs a JSON representation.

### Execute an AIXML Pipeline

```
python -m aixml --execute examples/complex1.xml
```
- Executes the pipeline defined in the XML file.

### Run an Arbitrary Query

```
python -m aixml --ask "What is the capital of France?"
```
- Sends a prompt directly to the LLM backend.

### Additional Options

- `--encoding` (default: utf-8): Specify text encoding
- `--overwrite`: Allow overwriting output files
- `--quiet`: Suppress non-error messages

## Syntax Reference

- `<pipeline>`: Defines a workflow pipeline
- `<set-variable output_var="...">value</set-variable>`: Sets a variable
- `<interpret-as-bool input_var="..." output_var="..." />`: Interprets input as boolean using LLM
- `<continue-if condition="...">...</continue-if>`: Conditional execution
- `<debug>...</debug>`: Prints debug information
- `<write-to-file filename="...">...</write-to-file>`: Writes output to a file

See the `examples/` directory for more sample pipelines and advanced usage.

## Project Status

AIXML is intended for experimentation and prototyping. It is not production-ready. Contributions and feedback are welcome!
