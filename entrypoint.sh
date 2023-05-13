#!/bin/sh -l
python /main.py \
--openai_api_key "$1" \
--github_token "$2" \
--github_pr_id "$3" \
--files "$4" \
--openai_model "$5" \
--openai_temperature "$6" \
--openai_max_tokens "$7"
--logging "$8"
