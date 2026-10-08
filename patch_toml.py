import re

with open('/Users/jck/WORK/DEV/company-crewai-amp-v2/admin/company-flow-server/pyproject.toml', 'r') as f:
    content = f.read()

deps_to_relax = [
    "torch", "transformers", "onnx", "onnxruntime", "numpy", 
    "langchain-ollama", "langchain", "langchain-community", 
    "langchain-text-splitters", "pypdf", "boto3", "chromadb", 
    "langchain-openai", "langchain-aws"
]

for dep in deps_to_relax:
    content = re.sub(rf'"{dep}>=[^"]+"', f'"{dep}"', content)

with open('/Users/jck/WORK/DEV/company-crewai-amp-v2/admin/company-flow-server/pyproject.toml', 'w') as f:
    f.write(content)
