"""Deterministic routing for range-gated curve candidates."""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Literal, TypeAlias


if TYPE_CHECKING:
    from collections.abc import Mapping


AxisTransform: TypeAlias = Literal['linear', 'log10']
BlendWeighting: TypeAlias = Literal['linear', 'smoothstep']
BoundaryMember: TypeAlias = Literal['left', 'right']
_MIN_MEMBERS = 2
_MAX_ACTIVE_MEMBERS = 2


class RoutingError(ValueError):
    """Raised when a composite curve cannot route an axis value unambiguously."""


@dataclass(frozen=True)
class Interval:
    """Finite interval on a composite curve's canonical axis."""

    lower: float
    upper: float
    lower_inclusive: bool = True
    upper_inclusive: bool = True

    def __post_init__(self) -> None:
        """Validate the interval bounds."""
        if not math.isfinite(self.lower) or not math.isfinite(self.upper):
            message = 'Composite intervals must have finite bounds.'
            raise ValueError(message)
        if self.lower >= self.upper:
            message = 'A composite interval lower bound must be below its upper bound.'
            raise ValueError(message)

    def contains(self, value: float) -> bool:
        """Return whether a finite axis value belongs to the interval."""
        if not math.isfinite(value):
            return False
        above_lower = value > self.lower or (self.lower_inclusive and value == self.lower)
        below_upper = value < self.upper or (self.upper_inclusive and value == self.upper)
        return above_lower and below_upper

    def contains_interval(self, other: Interval) -> bool:
        """Return whether another interval is wholly contained in this interval."""
        lower_allowed = other.lower > self.lower or (
            other.lower == self.lower and (self.lower_inclusive or not other.lower_inclusive)
        )
        upper_allowed = other.upper < self.upper or (
            other.upper == self.upper and (self.upper_inclusive or not other.upper_inclusive)
        )
        return lower_allowed and upper_allowed


@dataclass(frozen=True)
class Contribution:
    """One atomic member and its weight at a routed curve point."""

    member_id: str
    weight: float


@dataclass(frozen=True)
class HardSwitchTransition:
    """Choose one of two overlapping members at a fixed axis value."""

    left_member: str
    right_member: str
    at: float
    boundary_member: BoundaryMember

    def __post_init__(self) -> None:
        """Validate the switch value and boundary owner."""
        if not math.isfinite(self.at):
            message = 'A hard-switch value must be finite.'
            raise ValueError(message)
        if self.boundary_member not in ('left', 'right'):
            message = 'A hard-switch boundary member must be left or right.'
            raise ValueError(message)

    def route(self, value: float) -> tuple[Contribution, ...]:
        """Route a value across the hard switch."""
        if value < self.at or (value == self.at and self.boundary_member == 'left'):
            return (Contribution(self.left_member, 1.0),)
        return (Contribution(self.right_member, 1.0),)


@dataclass(frozen=True)
class BlendTransition:
    """Blend two overlapping members over an explicit axis interval."""

    left_member: str
    right_member: str
    interval: Interval
    weighting: BlendWeighting = 'linear'

    def __post_init__(self) -> None:
        """Validate the weighting rule."""
        if self.weighting not in ('linear', 'smoothstep'):
            message = 'A blend weighting must be linear or smoothstep.'
            raise ValueError(message)

    def route(self, value: float, transform: AxisTransform) -> tuple[Contribution, ...]:
        """Route or blend a value across the declared transition."""
        if value < self.interval.lower or (
            value == self.interval.lower and not self.interval.lower_inclusive
        ):
            return (Contribution(self.left_member, 1.0),)
        if value > self.interval.upper or (
            value == self.interval.upper and not self.interval.upper_inclusive
        ):
            return (Contribution(self.right_member, 1.0),)

        lower = _transform(self.interval.lower, transform)
        upper = _transform(self.interval.upper, transform)
        position = (_transform(value, transform) - lower) / (upper - lower)
        if self.weighting == 'smoothstep':
            position = position * position * (3.0 - 2.0 * position)
        return (
            Contribution(self.left_member, 1.0 - position),
            Contribution(self.right_member, position),
        )


Transition: TypeAlias = HardSwitchTransition | BlendTransition


@dataclass(frozen=True)
class RangeGatedRouter:
    """Resolve members and weights without observing target values."""

    members: Mapping[str, Interval]
    transitions: tuple[Transition, ...]
    transform: AxisTransform = 'linear'

    def __post_init__(self) -> None:
        """Freeze member definitions and validate every transition."""
        if self.transform not in ('linear', 'log10'):
            message = 'A composite axis transform must be linear or log10.'
            raise ValueError(message)
        members = MappingProxyType(dict(self.members))
        object.__setattr__(self, 'members', members)
        if len(members) < _MIN_MEMBERS:
            message = 'A range-gated curve requires at least two members.'
            raise ValueError(message)
        if self.transform == 'log10' and any(interval.lower <= 0 for interval in members.values()):
            message = 'A log10 composite axis requires positive member intervals.'
            raise ValueError(message)
        transition_pairs: set[frozenset[str]] = set()
        for transition in self.transitions:
            self._validate_transition(transition)
            pair = frozenset((transition.left_member, transition.right_member))
            if pair in transition_pairs:
                message = f'Multiple transitions are defined for member pair {tuple(sorted(pair))}.'
                raise ValueError(message)
            transition_pairs.add(pair)

    def route(self, value: float) -> tuple[Contribution, ...]:
        """Return the atomic contribution weights for one canonical axis value."""
        active = tuple(
            member_id for member_id, interval in self.members.items() if interval.contains(value)
        )
        if not active:
            message = f'No composite member covers axis value {value}.'
            raise RoutingError(message)
        if len(active) == 1:
            return (Contribution(active[0], 1.0),)
        if len(active) > _MAX_ACTIVE_MEMBERS:
            message = f'More than two composite members cover axis value {value}: {active}.'
            raise RoutingError(message)

        active_pair = frozenset(active)
        matching = tuple(
            transition
            for transition in self.transitions
            if frozenset((transition.left_member, transition.right_member)) == active_pair
        )
        if len(matching) != 1:
            message = f'Expected one transition for active members {active}; found {len(matching)}.'
            raise RoutingError(message)
        transition = matching[0]
        if isinstance(transition, BlendTransition):
            return transition.route(value, self.transform)
        return transition.route(value)

    def _validate_transition(self, transition: Transition) -> None:
        pair = (transition.left_member, transition.right_member)
        if pair[0] == pair[1]:
            message = 'A transition must reference two different members.'
            raise ValueError(message)
        if any(member_id not in self.members for member_id in pair):
            message = f'Transition references an unknown member: {pair}.'
            raise ValueError(message)

        left = self.members[transition.left_member]
        right = self.members[transition.right_member]
        if isinstance(transition, BlendTransition):
            if not left.contains_interval(transition.interval) or not right.contains_interval(
                transition.interval
            ):
                message = 'A blend interval must be contained in both member intervals.'
                raise ValueError(message)
            _transform(transition.interval.lower, self.transform)
            _transform(transition.interval.upper, self.transform)
        elif not left.contains(transition.at) or not right.contains(transition.at):
            message = 'A hard-switch value must belong to both member intervals.'
            raise ValueError(message)


def _transform(value: float, transform: AxisTransform) -> float:
    if transform == 'log10':
        if value <= 0:
            message = 'A log10 composite axis requires positive values.'
            raise ValueError(message)
        return math.log10(value)
    return value
