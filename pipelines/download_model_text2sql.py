# from transformers import AutoTokenizer, AutoModelForCausalLM
# import os

# os.environ["HF_TOKEN"] = ""
# os.environ["HF_HUB_TIMEOUT"] = "1800"

# model_name = "Snowflake/Arctic-Text2SQL-R1-7B"
# cache_dir = "./local_models/arctic-text2sql"

# tokenizer = AutoTokenizer.from_pretrained(model_name, token=os.environ["HF_TOKEN"], cache_dir=cache_dir)
# model = AutoModelForCausalLM.from_pretrained(model_name, token=os.environ["HF_TOKEN"], cache_dir=cache_dir)
