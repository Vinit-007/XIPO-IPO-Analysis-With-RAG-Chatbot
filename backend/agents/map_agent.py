import os
import json
import time
import requests
from tools.token_utils import estimate_json_tokens, chunk_data_by_tokens, MAX_INPUT_TOKENS

# Cerebras API config
CEREBRAS_API_KEY = "csk-e8der3hkvt6hn2w6efr48d6wx6w9d98tey4t49n5jvvx3wtp"
CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
MODEL = "llama-3.3-70b"
TPM_SLEEP = 5  # seconds


def process_single_chunk(section_name: str, data, chunk_num: int = None, total_chunks: int = None, prompt_template: str = None):
    """
    Process a single chunk with OpenRouter API.
    Uses custom prompt_template if provided, otherwise uses default.
    """
    section_label = section_name
    if chunk_num is not None:
        section_label = f"{section_name} (Part {chunk_num}/{total_chunks})"
    
    # Use custom prompt template if provided
    if prompt_template:
        prompt = f"""You are an IPO research analyst.

Generate the section: {section_label}

{prompt_template.format(data=json.dumps(data, indent=2))}

Rules:
- Use ONLY the provided data
- Do NOT invent numbers
- If data is missing, say "Not disclosed"
"""
    else:
        prompt = f"""
You are an IPO research analyst.

Generate ONLY the section titled:
{section_label}

Rules:
- Use ONLY the provided data
- Do NOT invent numbers
- If data is missing, say "Not disclosed"
- Use bullet points or tables where appropriate
- Be concise and factual

DATA:
{json.dumps(data, indent=2)}
"""

    # Log token size
    prompt_tokens = estimate_json_tokens(prompt)
    print(f"   📊 Prompt size: ~{prompt_tokens} tokens")
    
    max_retries = 3
    base_delay = 5
    
    for attempt in range(max_retries):
        try:
            print(f"   🌐 Calling Cerebras API for: {section_label} (Attempt {attempt+1}/{max_retries})...")
            response = requests.post(
                CEREBRAS_URL,
                headers={"Authorization": f"Bearer {CEREBRAS_API_KEY}"},
                json={
                    "model": MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 2000
                },
                timeout=60
            )
            result = response.json()
            
            if "error" in result:
                raise Exception(result["error"].get("message", "Unknown error"))
            
            content = result["choices"][0]["message"]["content"]
            print(f"   ✅ API call successful")
            return content
        except Exception as e:
            print(f"   ❌ API call failed: {str(e)}")
            if attempt < max_retries - 1:
                sleep_time = base_delay * (2 ** attempt)
                print(f"   ⏳ Retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                print("   💀 Max retries reached. Moving to next chunk or failing.")
                return f"[FAILED TO GENERATE SECTION: {section_label}]"


def run_map_stage(chunks):
    """
    Process all chunks with automatic hierarchical chunking for oversized sections.
    """
    partial_outputs = []
    total_sections = len(chunks)

    for i, chunk in enumerate(chunks, 1):
        section_name = chunk.get('section', f'Section {i}')
        data = chunk.get('data', {})
        prompt_template = chunk.get('prompt_template', None)
        
        print(f"🧠 MAP {i}/{total_sections} — {section_name}")

        # Estimate tokens for this chunk
        data_tokens = estimate_json_tokens(data)
        
        # If under limit, process normally
        if data_tokens <= MAX_INPUT_TOKENS:
            result = process_single_chunk(section_name, data, prompt_template=prompt_template)
            partial_outputs.append(result)
        else:
            # Hierarchical chunking needed
            print(f"⚠️  {section_name} too large ({data_tokens} tokens) — hierarchical chunking")
            
            # Split data into smaller chunks
            sub_chunks = chunk_data_by_tokens(data, MAX_INPUT_TOKENS)
            sub_results = []
            
            for j, sub_data in enumerate(sub_chunks, 1):
                print(f"   ↳ Sub-chunk {j}/{len(sub_chunks)}")
                sub_result = process_single_chunk(section_name, sub_data, j, len(sub_chunks), prompt_template)
                sub_results.append(sub_result)
                
                # Sleep between sub-chunks (except last)
                if j < len(sub_chunks):
                    print(f"   ⏳ Sleeping {TPM_SLEEP}s (TPM safety)")
                    time.sleep(TPM_SLEEP)
            
            # Combine sub-results
            combined_result = f"# {section_name}\n\n" + "\n\n".join(sub_results)
            partial_outputs.append(combined_result)

        # Sleep between main chunks (except last)
        if i < total_sections:
            print(f"⏳ Sleeping {TPM_SLEEP}s (TPM safety)")
            time.sleep(TPM_SLEEP)

    return partial_outputs

