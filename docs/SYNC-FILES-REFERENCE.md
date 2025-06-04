# Template Sync: What Files Are Updated

## Files That WILL BE SYNCED (Overwritten)

### 🔧 GitHub Configuration
```
.github/
├── workflows/
│   ├── sync-from-template.yml     ✅ Always updated
│   ├── sync-to-downstream.yml     ✅ (Template repo only)
│   └── template-cleanup.yml       ✅ (Template repo only)
├── CODEOWNERS                     ✅ Always updated
└── (any other .github files)     ✅ Always updated
```

### 📚 Documentation & References
```
reference/
├── api-registry.yaml              ✅ Always updated
├── validation-guide.md            ✅ Always updated
├── cheatsheet.md                  ✅ Always updated
└── template-sync.md               ✅ Always updated

guide/
├── instructions/                  ✅ Always updated
│   ├── solution-development.md
│   ├── best-practices.md
│   └── checklists.md
├── adr/                          ✅ Always updated
├── mistakes/                     ✅ Always updated
└── prd/                          ✅ Always updated
```

### 🎯 Solution Templates
```
templates/
├── basic_etl/                     ✅ Always updated
├── api_integration/               ✅ Always updated
├── ai_analysis/                   ✅ Always updated
└── README.md                      ✅ Always updated
```

### 🔗 Shared Components
```
src/
├── __init__.py                    ✅ Always updated
└── shared/                        🔄 MERGED (preserves custom additions)
    ├── __init__.py                ✅ Template version used
    ├── nodes/                     🔄 MERGED (your custom nodes preserved)
    ├── utils/                     🔄 MERGED (your custom utils preserved)
    └── workflows/                 🔄 MERGED (your custom workflows preserved)
```

### 🛠️ Core Scripts
```
scripts/
├── setup_env.py                   ✅ Always updated
├── validate.py                    ✅ Always updated
└── deploy.py                      ✅ Always updated
```

### 📋 Configuration Files
```
.pre-commit-config.yaml            ✅ Always updated
MANIFEST.in                        ✅ Always updated
pyproject.toml                     🔄 MERGED (preserves your deps)
```

## Files That WILL BE PRESERVED (Never Touched)

### 💻 Your Solution Code
```
src/solutions/                     🛡️ NEVER TOUCHED
├── your_project/
├── client_work/
└── any_custom_solutions/
```

### 📊 Your Data
```
data/                              🛡️ YOUR FILES PRESERVED
├── samples/                       🆕 Template samples added if missing
├── configs/                       🆕 Template configs added if missing  
├── outputs/                       🛡️ Your outputs preserved
└── your_project_data/             🛡️ NEVER TOUCHED
```

### ⚙️ Your Environment
```
.env                               🛡️ NEVER TOUCHED
.env.local                         🛡️ NEVER TOUCHED
.env.production                    🛡️ NEVER TOUCHED
config.yaml                        🛡️ NEVER TOUCHED
```

### 🔧 Your Custom Workflows
```
.github/workflows/
├── my_deployment_custom.yml       🛡️ NEVER TOUCHED (*_custom.yml)
├── my_testing_custom.yml          🛡️ NEVER TOUCHED (*_custom.yml)
└── any_other_workflow.yml         ⚠️ WILL BE OVERWRITTEN
```

## Files Added If Missing (Preserve Existing)

### 📝 Documentation Structure
```
todos/                             🆕 ADDED IF MISSING
├── 000-master.md                  🛡️ Preserved if exists
└── completed-archive.md           🛡️ Preserved if exists

examples/                          🆕 ADDED IF MISSING  
├── _utils/                        🛡️ Your examples preserved
│   └── test_all_examples.py       🆕 Added if missing
└── your_examples/                 🛡️ NEVER TOUCHED

docs/                              🆕 ADDED IF MISSING
├── api/                           🛡️ Your docs preserved
├── guides/                        🛡️ Your guides preserved
└── build_docs.py                  🆕 Added if missing

CHANGELOG.md                       🆕 ADDED IF MISSING
```

## Special Merge Handling

### 🔄 README.md
- Template structure merged with your content
- Your project-specific sections between markers are preserved:
```markdown
<!-- PROJECT SPECIFIC START -->
Your content here is NEVER touched
<!-- PROJECT SPECIFIC END -->
```

### 🔄 pyproject.toml
- Template dependencies are added
- Your project dependencies are preserved
- Your project metadata (name, version) is kept

### 🔄 CLAUDE.md
- Template instructions are updated
- Your project-specific instructions after `## Project-Specific Instructions` are preserved

### 🔄 src/shared/
- Template shared components are updated
- Your custom nodes, utils, workflows are preserved
- New template components are added alongside yours

## Summary for New vs Existing Repositories

### New Repository (from template):
- ✅ Gets complete structure
- ✅ All folders and files created
- ✅ Ready to use immediately

### Existing Repository (like ai_coaching):
- ✅ Gains template infrastructure
- 🛡️ All existing code preserved
- 🆕 Missing structure added
- 🔄 Compatible files merged

**Key Point**: Nothing is ever deleted. Template sync only adds or updates files, preserving all your existing work.