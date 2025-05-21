import base64
from openai import OpenAI


api_key = "c66bc18de21811217e5efa97085dae33b0028ef845e72301a054c9850221a3b0"
api_base = "https://api.together.xyz/v1/"
client = OpenAI(api_key=api_key, base_url=api_base)
model="meta-llama/Llama-4-Scout-17B-16E-Instruct"
# prompt = f"Differences have been marked in the following picture, please streamline the summary of the differences and output the summary conclusions, the output format is a separate div tag content in html format, the content is required to be neat and beautiful, and the content is displayed on the left."
prompt = f"以下图片中已经标记出了差异点，请对差异内容进行精简总结并输出英文的总结结论，输出格式为html格式的独立div标签内容，要求内容整洁美观，内容靠左显示。"

def summarize_image(image_base64) -> str:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}"
                            },
                        },
                    ],
                }
            ],
            max_tokens=1024,
        )
        return response.choices[0].message.content