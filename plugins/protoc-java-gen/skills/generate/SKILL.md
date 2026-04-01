---
name: generate
description: "Generate Java from a .proto file using protoc and auto-copy to matching subprojects. Use when user says 'generate proto', 'run protoc', 'compile proto', or provides a .proto filename."
allowed-tools:
  - Bash
  - Read
disable-model-invocation: true
argument-hint: "[file.proto]"
---

# Generate protoc-java-gen

Parse the proto filename from ARGUMENTS and run:

```bash
bash "${CLAUDE_PLUGIN_ROOT}/scripts/generate.sh" ${ARGUMENTS}
```

If no argument is provided, the script lists available .proto files.
