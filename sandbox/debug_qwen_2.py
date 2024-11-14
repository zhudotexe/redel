from transformers import AutoModelForCausalLM, AutoTokenizer

prompt = (
    "<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. You are a helpful"
    " assistant.<|im_end|>\n<|im_start|>user\nWhat are the names of 6 Metropolitan cities in Korea and their respective"
    ' symbol flowers?<|im_end|>\n<|im_start|>assistant\n<tool_call>\n{"name": "search", "arguments": {"query": "6'
    " Metropolitan cities in Korea and their symbol"
    " flowers\"}}\n</tool_call><|im_end|>\n<|im_start|>user\n<tool_response>\nThe function 'search' is not defined."
    " Only use the provided functions.\n</tool_response><|im_end|>\n<|im_start|>assistant\n"
)

model_name = "Qwen/Qwen2.5-72B-Instruct"
model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype="auto", device_map="auto")
tokenizer = AutoTokenizer.from_pretrained(model_name)

model_inputs = tokenizer([prompt], return_tensors="pt").to(model.device)

generated_ids = model.generate(**model_inputs, max_new_tokens=512)
generated_ids = [output_ids[len(input_ids) :] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)]

response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
