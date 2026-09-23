# Extension Guide

## Add a new device

1. Create a device adapter.
2. Implement the common device interface.
3. Implement connection/capability checks.
4. Implement configuration collection.
5. Add device-specific normalization/parsing only where needed.
6. Add tests.

## Add a new benchmark

1. Upload/store the benchmark through the benchmark subsystem.
2. Ensure its control metadata maps to the shared control model.
3. Add specialized evaluation logic only if the generic engine cannot express the control.
4. Add deterministic tests.

## Add a new AI provider

1. Create a provider adapter.
2. Keep provider SDK imports inside that adapter.
3. Expose the same application-level AI contract.
4. Preserve deterministic fallback behavior.

## Add a frontend feature

The frontend should call the API rather than reaching into backend implementation details. Keep UI state separate from compliance/business logic.

## Parallel development

Developers should work by module or feature branch. Shared contracts in `shared/` should change deliberately because they are the integration boundary for multiple modules.
