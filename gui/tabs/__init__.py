# gui/tabs/__init__.py
"""
GUI Tabs Package
Contains tabbed interface components including Team Trials
"""

from .strategy_tab import StrategyTab
from .event_choice_tab import EventChoiceTab
from .team_trials_tab import TeamTrialsTab

__all__ = [
    'StrategyTab',
    'EventChoiceTab',
    'TeamTrialsTab'
]