@echo off
REM agents.bat - Script único para gestión de agentes IA
REM Uso: agents.bat [setup|sync]
setlocal enabledelayedexpansion

if "%1"=="" (
    echo.
    echo Uso: agents.bat [comando]
    echo.
    echo Comandos disponibles:
    echo   setup  - Configuracion inicial de agentes ^(ejecutar 1 vez^)
    echo   sync   - Sincronizar metadata de skills ^(usar frecuentemente^)
    echo.
    exit /b 1
)

if /i "%1"=="setup" goto :setup
if /i "%1"=="sync" goto :sync

echo Error: Comando desconocido "%1"
exit /b 1

REM =============================================================================
REM SETUP - Configuración inicial
REM =============================================================================
:setup
echo.
echo 🤖 Setup de Agentes IA
echo ======================
echo.

cd /d "%~dp0"
set AGENTS=claude copilot gemini cursor

REM Crear carpetas y symlinks
for %%a in (%AGENTS%) do (
    if not exist ".%%a" mkdir ".%%a"
    if exist ".%%a\skills" rmdir ".%%a\skills" 2>nul || rd /s /q ".%%a\skills" 2>nul
    mklink /J ".%%a\skills" "%cd%\skills" >nul 2>&1
    copy /Y "agents.md" ".%%a\%%a.md" >nul
    powershell -Command "(Get-Content '.%%a\%%a.md') -replace '/skills/', './skills/' | Set-Content '.%%a\%%a.md'" >nul 2>&1
    echo ✓ .%%a configurado
)

echo.
echo ✓ Setup completado
echo Ejecuta: agents.bat sync
echo.
exit /b 0

REM =============================================================================
REM SYNC - Sincronización de metadata
REM =============================================================================
:sync
echo.
echo 🔄 Sincronizacion de Skills
echo ===========================
echo.

cd /d "%~dp0"

REM Crear script PowerShell temporal
(
echo $skills = @^(^)
echo Get-ChildItem -Path 'skills' -Directory ^| ForEach-Object {
echo     $skillName = $_.Name
echo     $skillFile = Join-Path $_.FullName 'skill.md'
echo     if ^(-not ^(Test-Path $skillFile^)^) { $skillFile = Join-Path $_.FullName 'README.md' }
echo     if ^(Test-Path $skillFile^) {
echo         $content = Get-Content $skillFile -Raw
echo         $name = if ^($content -match '- \*\*Name:\*\* (.+^)'^) { $matches[1] -replace '`', '' } else { $skillName }
echo         $desc = if ^($content -match '- \*\*Description:\*\* (.+^)'^) { $matches[1] -replace '`', '' } else { "Skill para $skillName" }
echo         $trigger = if ^($content -match '- \*\*Trigger:\*\* (.+^)'^) { $matches[1] -replace '`', '' } else { 'Manual' }
echo         $scope = if ^($content -match '- \*\*Scope:\*\* (.+^)'^) { $matches[1] -replace '`', '' } else { 'general' }
echo         Write-Host "  ✓ $name" -ForegroundColor Green
echo         $skills += [PSCustomObject]@{ Name=$name; Description=$desc; Trigger=$trigger; Scope=$scope }
echo     }
echo }
echo $table = "^<^!-- SKILLS_TABLE_START --^>`n^| Trigger ^| Skill ^| Scope ^| Descripcion ^|`n^|---------|-------|-------|-------------^|`n"
echo $skills ^| ForEach-Object { $table += "^| $^($_.Trigger^) ^| $^($_.Name^) ^| $^($_.Scope^) ^| $^($_.Description^) ^|`n" }
echo $table += "^<^!-- SKILLS_TABLE_END --^>"
echo $content = Get-Content 'agents.md' -Raw
echo $content = $content -replace '(?s^)^<^!-- SKILLS_TABLE_START --^>.*^<^!-- SKILLS_TABLE_END --^>', $table
echo Set-Content 'agents.md' -Value $content -NoNewline
echo $agents = @^('claude', 'copilot', 'gemini', 'cursor'^)
echo foreach ^($agent in $agents^) {
echo     $agentFile = ".$agent/$agent.md"
echo     if ^(Test-Path $agentFile^) {
echo         $content = Get-Content $agentFile -Raw
echo         $content = $content -replace '(?s^)^<^!-- SKILLS_TABLE_START --^>.*^<^!-- SKILLS_TABLE_END --^>', $table
echo         Set-Content $agentFile -Value $content -NoNewline
echo     }
echo }
echo Write-Host "`n✓ Skills: $^($skills.Count^) sincronizadas" -ForegroundColor Green
) > _sync_temp.ps1

powershell -ExecutionPolicy Bypass -File _sync_temp.ps1
del _sync_temp.ps1 >nul 2>&1

echo.
exit /b 0
