# PowerShell script to remove duplicate files from the APF repository
# Keeps main repository files, removes BU_TOOL duplicates

$duplicates = @(
    "BU_TOOL/tests/schemas/test_diagnostics_schema.py",
    "BU_TOOL/tests/registries/test_actors_registry.py", 
    "BU_TOOL/tests/registries/test_actions_registry.py",
    "BU_TOOL/packages/import_export/loaders.py",
    "BU_TOOL/packages/apf_core/__init__.py",
    "BU_TOOL/packages/apf_core/validation.py",
    "BU_TOOL/packages/import_export/exporters/drawio.py",
    "BU_TOOL/packages/apf_core/models.py",
    "BU_TOOL/packages/import_export/exporters/json_exporter.py",
    "BU_TOOL/packages/import_export/exporters/markdown.py",
    "BU_TOOL/packages/import_export/exporters/yaml_exporter.py",
    "BU_TOOL/packages/apf_core/stepkey.py",
    "BU_TOOL/packages/apf_core/sequencing.py",
    "BU_TOOL/packages/import_export/exporters/__init__.py",
    "BU_TOOL/packages/import_export/__init__.py",
    "BU_TOOL/registries/actions.yaml",
    "BU_TOOL/registries/actors.yaml",
    "BU_TOOL/schemas/diagnostics.schema.json",
    "apps/cli/apf/__init__.py",
    "apps/cli/apf/commands/export.py", 
    "apps/cli/apf/commands/validate.py",
    "apps/cli/apf/commands/watch.py",
    "apps/cli/apf/__main__.py",
    "apps/cli/apf/commands/seq.py",
    "apps/service/watch.py",
    "apps/service/main.py",
    "apps/service/routes.py", 
    "apps/desktop/editors/yaml_editor.py",
    "apps/desktop/ui_shell.py",
    "apps/desktop/main.py",
    "BU_TOOL/README.md",
    "BU_TOOL/specs/demo_atomic.yaml",
    "BU_TOOL/.github/workflows/ci.yml",
    "pythonscripts_&_OTHER/HUEY_P_PY_Document_Automation_System.py"
)

Write-Host "Starting duplicate file removal process..." -ForegroundColor Green
$removed = 0
$notFound = 0

foreach ($file in $duplicates) {
    if (Test-Path $file) {
        try {
            Remove-Item $file -Force
            Write-Host "Removed: $file" -ForegroundColor Yellow
            $removed++
        }
        catch {
            Write-Host "Failed to remove: $file" -ForegroundColor Red
        }
    } else {
        Write-Host "Not found: $file" -ForegroundColor Gray
        $notFound++
    }
}

Write-Host ""
Write-Host "Summary:" -ForegroundColor Green
Write-Host "Files removed: $removed" -ForegroundColor Yellow
Write-Host "Files not found: $notFound" -ForegroundColor Gray
Write-Host "Duplicate removal complete!" -ForegroundColor Green