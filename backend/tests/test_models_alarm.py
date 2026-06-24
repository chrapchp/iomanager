###################################################
# Project:     IOManager
# Author:      Peter Chrapchynski
# Date:        2026Jun23
# History:     2026Jun23 - Initial creation
###################################################

import pytest
from pydantic import ValidationError
from app.models.alarm import Alarm, AlarmOptions, FilterConfig


def _make_alarm(**kwargs) -> Alarm:
    defaults = dict(tag_name="DIG_001", condition="POS", message="Test alarm")
    return Alarm(**(defaults | kwargs))


# ---------------------------------------------------------------------------
# Message validation
# ---------------------------------------------------------------------------

class TestAlarmMessageValidation:
    def test_message_at_120_chars_accepted(self):
        alarm = _make_alarm(message="A" * 120)
        assert len(alarm.message) == 120

    def test_message_at_121_chars_rejected(self):
        with pytest.raises(ValidationError):
            _make_alarm(message="A" * 121)

    def test_empty_message_accepted(self):
        alarm = _make_alarm(message="")
        assert alarm.message == ""


# ---------------------------------------------------------------------------
# Condition values
# ---------------------------------------------------------------------------

class TestAlarmCondition:
    def test_pos_condition_accepted(self):
        assert _make_alarm(condition="POS").condition == "POS"

    def test_neg_condition_accepted(self):
        assert _make_alarm(condition="NEG").condition == "NEG"

    def test_invalid_condition_rejected(self):
        with pytest.raises(ValidationError):
            _make_alarm(condition="INVALID")


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

class TestAlarmDefaults:
    def test_default_condition_is_pos(self):
        alarm = Alarm(tag_name="DIG_001")
        assert alarm.condition == "POS"

    def test_default_recipient(self):
        alarm = Alarm(tag_name="DIG_001")
        assert alarm.recipient == "Default"

    def test_default_handling_is_enabled(self):
        alarm = Alarm(tag_name="DIG_001")
        assert alarm.options.handling == "ENABLED"

    def test_default_filter_is_zero(self):
        alarm = Alarm(tag_name="DIG_001")
        assert alarm.filter.hours == 0
        assert alarm.filter.minutes == 0
        assert alarm.filter.seconds == 0

    def test_default_sms_acknowledge_is_false(self):
        alarm = Alarm(tag_name="DIG_001")
        assert alarm.options.sms_acknowledge is False

    def test_default_pop3_acknowledge_is_false(self):
        alarm = Alarm(tag_name="DIG_001")
        assert alarm.options.pop3_acknowledge is False

    def test_default_notify_end_of_alarm_is_true(self):
        alarm = Alarm(tag_name="DIG_001")
        assert alarm.options.notify_end_of_alarm is True


# ---------------------------------------------------------------------------
# AlarmOptions handling value
# ---------------------------------------------------------------------------

class TestAlarmOptions:
    def test_enabled_handling_accepted(self):
        opts = AlarmOptions(handling="ENABLED")
        assert opts.handling == "ENABLED"

    def test_disabled_handling_accepted(self):
        opts = AlarmOptions(handling="DISABLED")
        assert opts.handling == "DISABLED"

    def test_invalid_handling_rejected(self):
        with pytest.raises(ValidationError):
            AlarmOptions(handling="ON")
