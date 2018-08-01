.PHONY: train-core train-core-debug cmdline cmdline-debug

TEST_PATH=./

help:
	@echo "    train-core"
	@echo "        Trains a new dialogue model using the story training data"
	@echo "    cmdline"
	@echo "        Runs the bot on the cmdline"

train-core:
	python -m rasa_core.train -d domain.yml -s restaurant_plan.md -o forms_bot --epochs 1000 --validation_split 0 --augmentation 5

train-core-debug:
	python -m rasa_core.train -d domain.yml -s restaurant_plan.md -o forms_bot --epochs 1000 --validation_split 0 --augmentation 5 --debug

cmdline-debug:
	python -m rasa_core.run -c cmdline -d forms_bot/ --debug

cmdline:
	python -m rasa_core.run -c cmdline -d forms_bot/