# Forms Bot

## Installation
This bot requires the plans branch of core to be installed, i.e. https://github.com/RasaHQ/rasa_core/tree/plans. Otherwise it should work out of the box.

## Simple
In this repo we use the plans branch of core to implement deterministic form-filling, to exemplify how we intend for Forms to be used. For clarity, throughout the word Form refers to the object which supercedes the ML policy to make deterministic predictions. The headline is that if you need slots filled in a deterministic way then Forms are a good way of doing it. The way the stories are written for forms also makes it possible to change the required slots and behaviour afterwards without needing to rewrite stories. 

This is similar to what we were trying to do with FormActions, but differs in some ways:
- the actions required to fill the form do not need to be written into the stories, and therefore can be amended, reduced or increased with no changes to stories
- no magic words are required as all questioning intents are defined with their associated slots
- conditional logic for which slots need to be filled
- deterministic: when a plan is active, no ML predictions are made at all (besides intent and entities found with NLU)

### Forms object
The most simple format of Forms need only 4 things defined:
1. `name`: the name of the Form
2. `slot_dict`: a dictionary: `{'FIRST_SLOT_NAME': {'ask_utt': 'WHICH_UTTERANCE_ASKS_FOR_SLOT'}, 'SECOND_SLOT_NAME':.. }`, which ties together slot names and utterances. The bot will continue to ask about the unfilled slots until all the slots are filled or the form is otherwise exited.
3. `finish_action`: this is the name of the action that will be called when all of the relevant slots are filled. This action must return a EndPlan event but can do anything else alongside it.
4. `exit_dict`: the exit dict is a set of {'intent':'action'} pairs which describe what the bot should do in certain situations where the form should be exited.


### stories
We also need to let Rasa Core predict when to activate the Forms. We do this by defining an action (in this bot example `activate_restaurant` and `activate_hotel`) which contains a StartPlan event. We then write stories where this action is triggered:

```
## Generated Story 6817547858592778997
* request_restaurant
    - activate_restaurant
    - slot{"active_plan": true}
    - slot{"switch": false}
    - slot{"cuisine": "mexican"}
    - deactivate_plan
    - slot{"active_plan": false}
    - slot{"plan_complete": false}
    - utter_happy
* chitchat
    - utter_chitchat
* request_hotel
    - activate_hotel
```

which allows core to predict when to activate the restaurant. Using a combination of the finish_action or exit_dict one can featurize the way that the plan finished. In this case, we set a slot to say after an exit whether the form had been completed or not ('plan_complete'). It is important to note that *how* the slots were filled within the plan is not featurized. Simply which slots are filled at the time of the plan's deactivation is relevant and helps downstream core predictions. We see above an example of a story where the form has not been filled and the user has exited. We also have a story where the slots of the form have all been filled:

```
## Generated Story 7536939952037997255
* request_restaurant
    - activate_restaurant
    - slot{"active_plan": true}
    - slot{"switch": false}
    - slot{"location": "mcdonalds"}
    - slot{"price": "high"}
    - slot{"cuisine": "mcdonalds"}
    - deactivate_plan
    - slot{"active_plan": false}
    - slot{"plan_complete": true}
    - utter_filled_slots
    - utter_suggest_restaurant
* affirm
    - utter_book_restaurant
```

We see in this case since the `plan_complete` slot is set to true, we follow a different path when exiting.  There is more advanced functionality detailed below, but it is worth making sure you understand the basic functionality before moving on to that. A useful exercise would be to train and speak to the bot in this repo. you can do this by running:
```
make train-core

make cmdline-debug
```

and using the intent request_restaurant or request_hotel on the command line.

### Example output
Here is an example of the debug log for the cmdline bot.

```
Bot loaded. Type a message and press enter: 
request_restaurant
2018-08-01 09:50:12 DEBUG    rasa_core.tracker_store  - Creating a new tracker for id 'default'.
2018-08-01 09:50:12 DEBUG    rasa_core.processor  - Received user message 'request_restaurant' with intent '{'name': 'request_restaurant', 'confidence': 1.0}' and entities '[]'
2018-08-01 09:50:12 DEBUG    rasa_core.policies.memoization  - There is a memorised next action '48'
2018-08-01 09:50:12 DEBUG    rasa_core.policies.ensemble  - Predicted next action using policy_0_MemoizationPolicy
2018-08-01 09:50:12 DEBUG    rasa_core.policies.ensemble  - Predicted next action 'activate_restaurant' with prob 1.00.
2018-08-01 09:50:12 DEBUG    rasa_core.processor  - Action 'activate_restaurant' ended with events '['<rasa_core.events.StartPlan object at 0x123fc92b0>', 'SlotSet(key: active_plan, value: True)', 'SlotSet(key: switch, value: False)', 'SlotSet(key: plan_complete, value: False)']'
2018-08-01 09:50:12 DEBUG    rasa_core.policies.ensemble  - Plan restaurant_plan predicted next action UtterAction('utter_ask_price')
What price range?
```
The key lines to note are the rasa_core.policies.ensemble lines. The activation of the Form is predicted by the memoization policy and then the subsequent question asking is predicted by the Form. This will be the case until a StopPlan object is passed again.

## Complicated

### Advanced Forms object
There is added functionality which can be used:
1. `name` - as above
2. `slot_dict`: We can augment the dictionaries we assign to our slots like so:
`slot_dict = {'FIRST_SLOT_NAME': {'ask_utt': 'WHICH_UTTERANCE_ASKS_FOR_SLOT', "clarify_utt": 'WHICH_UTTERANCE_EXPLAINS_SLOT', "follow_up_action": "WHICH_ACTION_SHOULD_BE_PERFORMED_AFTER_USER_REPLIES"}, ...}`
    - `follow_up_action` will be performed after the user responds to `'ask_utt'`. This can be useful in some cases where you would like to ask a yes/no question. You can then have an action to deal with affirm/deny, such as `SpaAnswerParse` in `plan_actions.py`
    - `clarify_utt` will be said if the user asks for clarification, with `details_intent` (explained below)
3. `finish_action`: as above
4. `exit_dict`: as above
5. `chitchat_dict`: another {"intent":"action"} dictionary, however in this case the bot, when detecting the relevant intent, will do the corresponding action and then repeat their original question. OPTIONAL
6. `details_intent`: The intent which is asking for details about the previous question in the form fill. If the bot detects the details intent it will try to execute slot_dict['CURRENT_SLOT_NAME']['clarify_utt']. OPTIONAL
7. `rules`: a dictionary, defined as `{slot:{value:{keep:[slot,slot2], lose:[slot3]},...}, ...}` which, when matching slot/value pairs will alter which slots need to be filled to trigger the finish action of the Form. This is implemented in the restaurant form OPTIONAL

The Forms need to be made as objects and then referenced in the domain (see domain.yml here). Core will trigger the Form when your activate action is predicted, and stories/featurizer will ignore the intents/actions carried out within the Form, with the exception of slot setting.

### Advanced stories
In the example here the slots for location/price/cuisine etc. are unfeaturized, so adding another slot within the plan would not require rewriting the stories. Therefore to Rasa core the above story is equivalent to:

```
## Generated Story 7536939952037997255
* request_restaurant
    - activate_restaurant
    - slot{"active_plan": true}
    - slot{"switch": false}
    - deactivate_plan
    - slot{"active_plan": false}
    - slot{"plan_complete": true}
    - utter_filled_slots
    - utter_suggest_restaurant
* affirm
    - utter_book_restaurant
```

Therefore it is useful being deliberate about which slots you featurize and which you don't. I.e. like in this case, if the slots you want to fill are only relevant as arguments to an api-call, then it is advised to not featurize the slots and instead include an action which checks if all the slots are filled, such as `DeactivatePlan` in `plan_actions.py` and then store the result of this in a slot which will be featurized.


## How does it work really?

It is worthwhile taking a brief look at the Form object to understand the workflow and how the different arguments interact with one another. The full object is in rasa_core.policies.plans, but you can get an idea just from looking at the `next_action_idx` function:

```
    def next_action_idx(self, tracker, domain):
        # type: (DialogueStateTracker, Domain) -> int

        out = self._run_through_queue(domain)
        if out is not None:
            # still actions in queue
            return out

        intent = tracker.latest_message.parse_data['intent']['name'].replace('plan_', '', 1)
        self._update_requirements(tracker)

        if intent in self.exit_dict.keys():
            # actions in this dict should deactivate this plan in the tracker
            self._exit_queue(intent, tracker)
            return self._run_through_queue(domain)

        elif intent in self.chitchat_dict.keys() and tracker.latest_action_name not in self.chitchat_dict.values():
            self._chitchat_queue(intent, tracker)
            return self._run_through_queue(domain)
        elif intent in self.details_intent and 'utter_explain' not in tracker.latest_action_name:
            self._details_queue(intent, tracker)
            return self._run_through_queue(domain)

        still_to_ask = self.check_unfilled_slots(tracker)

        if len(still_to_ask) == 0:
            self.queue = [self.finish_action, 'action_listen']
            return self._run_through_queue(domain)
        else:
            self.last_question = self._decide_next_question(still_to_ask, tracker)
            self.queue = self._question_queue(self.last_question)
            return self._run_through_queue(domain)
```

Forms work by queueing up a list of actions as soon as it is the bot's turn to speak again. There are several "queues" of actions that can be lined up. The most common one will be the _question_queue which contains the `ask_utt` for an unfilled slot and then listens (If there is a `follow_up_acton` the queue will have that action appended after the action_listen and will be the first action done before a new queue is made). Another queue is the finish queue, which will take the action listed as `finish_action` and execute it. The chitchat queue will, when presented with one of the keys of `chitchat_dict`, perform the corresponding action and then repeat the question it previously asked. the details queue will perform the 'clarify_utt' action, say the previous question and then listen when being provided the `details_intent`. The last queue is the exit dict which will, when presented with the intent key, perform the corresponding value action. The action itself must exit the Form by returning a StopPlan event.

We intend plans to be used as a majority slot-filling exercise, which means that all intents are ignored except in the cases that:
- your `follow_up_action` explicitly deals with the intent (see `SpaAnswerParse` in `plan_actions.py`)
- any intent which is in `[exit_dict.keys(), chitchat_dict.keys(), details_intent]` is detected.



