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

"Shelf" – Responsibilities & Verbs

Verb| Purpose| Examples
"import"| Bring PDFs into the shelf from external sources| Import files from a directory or another system
"load"| Read shelf state or metadata| Load YAML, JSON, or database records
"extract"| Read information from PDFs| Extract document metadata and properties
"sanitize"| Remove or normalize unsafe or unwanted content| Sanitize PDF structure and metadata
"update"| Modify metadata or shelf records| Update title, author, tags, or status
"copy"| Duplicate PDFs or metadata| Copy files to another location
"move"| Relocate managed files| Move PDFs into shelf storage
"rename"| Change managed filenames| Rename files using a naming convention
"publish"| Make book information available to other components| Publish book details to the UI or API
"save"| Persist shelf state| Save YAML, JSON, or database records
"write"| Write output files| Write a newly reconstructed PDF
"read"| Read input files| Read PDFs, YAML, JSON, or database entries
"export"| Produce data for external consumption| Export metadata or reports

Typical workflow

import → load → extract → sanitize → update → write → move → rename → save → publish → export

"ShelfDisplay" – Responsibilities & Interaction with "Shelf"

Responsibility

"ShelfDisplay" presents the contents and state of a "Shelf" to the user. It does not import, sanitize, move, or modify PDF files directly.

Interactions with "Shelf"

|Action| Purpose| Example
"load"| Obtain the current shelf state| Load books for display
"refresh"| Reload the view after shelf changes| Refresh the book list
"display"| Render shelf information| Display books, metadata, and status
"filter"| Show a subset of books| Filter by author or tag
"sort"| Change display order| Sort by title or year
"select"| Select one or more books| Select a book to inspect
"view"| Show detailed information| View book metadata
"search"| Find matching books| Search by title or ISBN
"notify"| Present shelf events| Show import or sanitize completion
"request"| Ask "Shelf" to perform an operation| Request import, sanitize, or rename
"observe"| Listen for shelf updates| Update UI when the shelf changes

Typical interaction

User
  │
  ▼
ShelfDisplay
  │ request
  ▼
Shelf
  │ performs operation
  ▼
ShelfDisplay
  │ refresh
  ▼
Display updated shelf information

Responsibilities

Shelf

- Imports PDFs
- Sanitizes PDFs and metadata
- Writes new PDFs
- Moves and renames files
- Reads and writes YAML/JSON/database
- Maintains the shelf state

ShelfDisplay

- Displays shelf contents
- Displays book details and status
- Filters, sorts, and searches books
- Handles user selection
- Requests operations from "Shelf"
- Refreshes when the "Shelf" changes