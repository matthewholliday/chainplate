from .external.prompt_completion_services.openai_llm_provider import OpenAIPromptCompletionService

class NaiveDataTypeService:
    
    @staticmethod
    def to_json_with_retry(payload: str, json_shape: str = None, max_retries: int = 3) -> str:
        prompt_service = OpenAIPromptCompletionService()
        prompt = NaiveDataTypeService.build_json_prompt(payload, json_shape)
        
        for attempt in range(max_retries):
            print(f"Attempt {attempt + 1} to convert payload to JSON.") # TODO: remove debug print statements in production code
            response = prompt_service.send_message(prompt)
            if NaiveDataTypeService.is_valid_json(response):
                return response
        
        raise ValueError("Failed to convert payload to valid JSON after multiple attempts.")

    @staticmethod
    def is_valid_json(json_string: str) -> bool:
        import json
        try:
            json.loads(json_string)
            return True
        except ValueError:
            return False

    @staticmethod
    def build_json_prompt(payload: str, json_shape: str = None) -> str:
        base_prompt = (
            "You are a helpful assistant that converts a given payload into valid JSON.\n\n"
            "Instructions:\n"
            "1. Always return well-formed JSON.\n"
            "2. Do not include explanations or extra text, only output valid JSON.\n"
            "3. If values are missing, make a reasonable guess or use null.\n"
        )
        
        if json_shape:
            base_prompt += f"4. Follow this expected JSON shape:\n{json_shape}\n\n"
        
        base_prompt += f"Here is the payload:\n{payload}\n\n"
        base_prompt += "Return the completed JSON only."
        
        return base_prompt
