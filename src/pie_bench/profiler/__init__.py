"""Profiler: an engine's forward pass, timed end to end from the device's own trace.

A profiled cell runs its standard benchmark rounds and then one short round under the platform's tracer, in the same
engine session, and reports per benchmark unit the wall time, the time the device was busy (the forward pass: the
union of every device work interval) and the rest (idle). No kernel names.
"""
