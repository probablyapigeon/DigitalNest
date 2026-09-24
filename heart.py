"""Time-scaled game emotion inspired by UnifiedHeartAgent, not a physical metric."""
import math


def initial_heart():
    return dict(psi=.5, theta=.5, light=.5, darkness=.5, heart=4.5, perturb=0., elapsed=0.)


def heart_event(state, stimulus, pressure=False):
    """An event changes state immediately; only simulation ticks advance time."""
    stimulus = max(0., min(1., stimulus))
    if pressure:
        state['darkness'] = min(1., state['darkness'] + .1*stimulus)
        state['perturb'] = min(1., state['perturb'] + .15*stimulus)
    else:
        state['light'] = min(1., state['light'] + .08*stimulus)
        state['perturb'] *= .9
    state['heart'] = state['psi'] * 9. * (state['light'] + state['darkness'])


def update_heart(state, stimulus, pressure=False, seconds=5.):
    if not math.isfinite(stimulus) or not math.isfinite(seconds) or seconds < 0:
        raise ValueError('Heart inputs must be finite and time cannot run backwards.')
    stimulus = min(1., max(0., stimulus))
    # Small substeps make a long rest equivalent to several short rests.
    remaining = seconds
    while remaining > 0:
        dt = min(1., remaining)
        inertia = math.exp(-dt / 90.)
        rate = 1. - inertia
        effective = stimulus - .1 * state['perturb']
        if pressure:
            state['darkness'] += rate * (abs(effective) - state['darkness'])
            state['light'] *= inertia
            state['perturb'] += rate * (abs(stimulus-.5)*2 - state['perturb'])
        else:
            state['light'] += rate * (effective - state['light'])
            state['darkness'] *= inertia
            state['perturb'] *= math.exp(-dt / 30.)
        state['theta'] += rate * ((stimulus-state['psi']) - state['theta'])
        state['psi'] += rate * (state['theta']*(state['light']-state['darkness']) - state['psi'])
        for name in ('light', 'darkness', 'perturb'):
            state[name] = min(1., max(0., state[name]))
        for name in ('psi', 'theta'):
            state[name] = min(1., max(-1., state[name]))
        state['elapsed'] += dt
        remaining -= dt
    state['heart'] = state['psi'] * 9. * (state['light'] + state['darkness'])
    return state


def description(state):
    if state['perturb'] > .35:
        return 'unsettled; seeking a quiet, reassuring interaction'
    if state['light'] > state['darkness'] + .15:
        return 'connected and open to company'
    return 'watchful and gently curious'
