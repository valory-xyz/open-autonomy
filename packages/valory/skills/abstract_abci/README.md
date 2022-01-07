# ABCI skill

## Description

This abstract skill provides a template of an ABCI application managed by
an AEA.

## Behaviours 

No behaviours (the skill is purely reactive).

## Handlers

- ABCIHandler \
  an abstract Handler that replies to ABCI requests with default responses.
  In another skill, extend the class and override the request handlers
  to implement a custom behaviour.
