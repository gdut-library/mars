.PHONY: dev manager

envvar=LIB_SERVER_CONFIG
config_path=$(shell pwd)/configurations
develop_config=$(config_path)/develop.py

dev:
	export $(envvar)='$(develop_config)' && python manage.py run

manager:
	export $(envvar)='$(develop_config)' && python manage.py
