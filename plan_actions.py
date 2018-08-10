from rasa_core.policies.plans import SimpleForm
from rasa_core.events import SlotSet, StartPlan, EndPlan
from rasa_core.actions import ActionStartPlan, Action


class RestaurantPlan(SimpleForm):
    def __init__(self):
        name = 'restaurant_plan'
        slot_dict = {"price": {"ask_utt": "utter_ask_price", "clarify_utt": "utter_explain_price_restaurant"},
                     "cuisine": {"ask_utt": "utter_ask_cuisine", "clarify_utt": "utter_explain_cuisine_restaurant"},
                     "people": {"ask_utt": "utter_ask_people", "clarify_utt": "utter_explain_people_restaurant"},
                     "location": {"ask_utt": "utter_ask_location", "clarify_utt": "utter_explain_location_restaurant"}}

        finish_action = "deactivate_plan"

        exit_dict = {"goodbye": "deactivate_plan",
                     "request_hotel": "deactivate_plan_switch"}

        chitchat_dict = {"chitchat": "utter_chitchat"}

        details_intent = "utter_ask_details"

        rules = {"cuisine":{"mcdonalds": {'need':['location'], 'lose':['people', 'price']}}}

        failure_action = 'utter_human_hand_off'
        super(RestaurantPlan, self).__init__(name, slot_dict, finish_action, exit_dict, chitchat_dict, details_intent, rules, failure_action=failure_action)


class HotelPlan(SimpleForm):
    def __init__(self):
        name = 'hotel_plan'
        slot_dict = {"startdate": {"ask_utt": "utter_ask_startdate", "clarify_utt": "utter_explain_startdate_hotel"},
                     "enddate": {"ask_utt": "utter_ask_enddate", "clarify_utt": "utter_explain_enddate_hotel"},
                     "location": {"ask_utt": "utter_ask_location", "clarify_utt": "utter_explain_location_hotel"},
                     "has_spa": {"ask_utt": "utter_ask_has_spa", "follow_up_action": "parse_spa"}}

        finish_action = 'deactivate_plan'

        exit_dict = {"goodbye": "deactivate_plan",
                     "request_restaurant": "deactivate_plan_switch"}

        chitchat_dict = {"chitchat": "utter_chitchat"}

        details_intent = 'utter_ask_details'

        rules = {}

        failure_action = 'utter_human_hand_off'

        super(HotelPlan, self).__init__(name, slot_dict, finish_action, exit_dict, chitchat_dict, details_intent, rules, failure_action=failure_action)

class StartRestaurantPlan(ActionStartPlan):

    def __init__(self):
        self._name = 'activate_restaurant'

    def run(self, dispatcher, tracker, domain):
        """Simple run implementation uttering a (hopefully defined) template."""
        return [StartPlan(domain, 'restaurant_plan')]

    def name(self):
        return self._name

    def __str__(self):
        return "ActivatePlan('{}')".format(self.name())


class StartHotelPlan(ActionStartPlan):
    def __init__(self):
        self._name = 'activate_hotel'

    def run(self, dispatcher, tracker, domain):
        """Simple run implementation uttering a (hopefully defined) template."""
        # tracker.activate_plan(domain)
        return [StartPlan(domain, 'hotel_plan')]

    def name(self):
        return self._name

    def __str__(self):
        return "ActivatePlan('{}')".format(self.name())


class StopPlanSwitch(Action):

    def __init__(self):
        self._name = 'deactivate_plan_switch'

    def run(self, dispatcher, tracker, domain):
        """Simple run implementation uttering a (hopefully defined) template."""
        # tracker.activate_plan(domain)
        return [EndPlan()]

    def name(self):
        return self._name

    def __str__(self):
        return "StopPlanSwitch('{}')".format(self.name())


class StopPlan(Action):
    def __init__(self):
        self._name = 'deactivate_plan'

    def run(self, dispatcher, tracker, domain):
        unfilled = tracker.active_plan.check_unfilled_slots(tracker)
        if len(unfilled) == 0:
            complete = True
        else:
            complete = False
        return [EndPlan(), SlotSet('plan_complete', complete)]

    def name(self):
        return self._name

    def __str__(self):
        return "StopPlanSwitch('{}')".format(self.name())


class SpaAnswerParse(Action):
    def __init__(self):
        self._name = 'parse_spa'

    def run(self, dispatcher, tracker, domain):
        if tracker.latest_message.intent['name'] == 'plan_affirm':
            return [SlotSet('has_spa', True)]
        elif tracker.latest_message.intent['name'] == 'plan_deny':
            return [SlotSet('has_spa', False)]
        else:
            return []

    def name(self):
        return self._name

    def __str__(self):
        return "SpaAnswerParse"
