# Monday Handoff — Next Steps

- Validate indices lookup across more competencies (1967 → recent)
- Implement SEFIP export (spec + first version)
- Add import flow for Access/SEFIP text files
- Build consolidated and conference reports
- Enhance dashboard with KPIs (total corrigido, JAM by period)
- Unit tests for `acumulado_indices()` and `calcular_fgts_atualizado()`

## Quick Run

```powershell
. .\.venv\Scripts\Activate.ps1
. .\scripts\set_env.ps1
python manage.py runserver
```

## Notes
- Indice is not rounded; only monetary results use 2 decimals.
- Supabase is the primary source; local fallback exists.
