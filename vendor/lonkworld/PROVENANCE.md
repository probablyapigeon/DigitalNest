# LonkWorld XC integration provenance

Source: `xembra-xc/desktop-lonkworld` in the user's existing workspace.

Copied: `LonkWorld.xc`, `xc_runtime.py`, `xc_procedures.py`, `xc_app_runtime.py`,
`lonk_engine.py`, `lonk_language.py`, `lonk_society.py`.

The XC application/procedure source, native runtime, procedure interpreter and
language/society forwarding modules are unchanged. `xc_app_runtime.py` and
`lonk_engine.py` use package-relative imports to coexist with LUMINA's distinct
runtime. `LonkWorld.from_dict` exposes the existing validated save loader for the
game's single atomic combined save, avoiding an intermediate temporary world file.

`flock_society.py` invokes the genuine XC procedures. It supplies a bounded,
nonlethal robot nursery using original language/society inheritance functions,
instead of running age-based replacement rebirth. It captures interpreter output
through that instance's print primitive, not process-global stdout redirection.

Original source files, applications, and LonkWorld saves are not modified.
This file records provenance, not a grant of redistribution rights.
