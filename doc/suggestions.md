| Function | Meaning | Direction |
|----------|---------|-----------|
| `load()` | Read data into memory | Storage → Memory |
| `save()` | Persist data | Memory → Storage |
| `publish()` | Make available to others (upload, distribute, send) | Internal → External |
| `import()` | Read external data into the application's model | External → Internal |
| `export()` | Write data in a format for another system | Internal → External |
| `copy()` | Duplicate data without changing it | Object → Object |
| `update()` | Modify an existing object with new values | Existing → Updated |
| `extract()` | Read or pull information from an object | Object → Data |
| `parse()` | Convert raw text/bytes into structured data | Raw → Structured |
| `serialize()` | Convert an object to bytes/text | Object → Raw |
| `deserialize()` | Convert bytes/text into an object | Raw → Object |
| `convert()` | Transform between formats | Format A → Format B |
| `merge()` | Combine multiple data sources | Many → One |
| `sync()` | Make two copies consistent | A ⇄ B |
| `clone()` | Create a deep copy | Object → Independent Copy |