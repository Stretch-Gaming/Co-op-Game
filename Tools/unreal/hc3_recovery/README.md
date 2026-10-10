# HC-3 preserved recovery scaffold

This delivery preserves the saved work from the cancelled revive/recovery slice.
It defines a health bridge interface and isolated recovery/test Blueprint scaffolds.
It does not implement health, revive, death recovery, production input, or cave placement.
The scaffolds have no production references and must not be treated as accepted gameplay.

The cancelled inventory and owned-package preservation records are retained here.
An unsaved, unowned BP_TestInteractable remains in the original dedicated editor;
that in-memory package is not included in this delivery. No global Save All is allowed.

Native combined-project compilation is required before merging this preservation slice.
Full HC-3 acceptance and health/Core integration remain pending under issue #9.
