# Contribution Guide

## Principle

Contribute by module and preserve module boundaries.

## Before changing a shared contract

Check all consumers of the contract and update tests/documentation together.

## Commit scope

Prefer small commits that represent one coherent change, such as:

- add pfSense capability check;
- add benchmark extraction field;
- add remediation validation rule;
- add verification test.

## Tests

Add or update tests for behavior changes. Do not replace an unavailable external integration with fabricated success data.

## Safety

Never commit credentials or live-device configuration containing secrets. Do not add code that executes arbitrary AI-generated commands without the safety and approval boundary.
