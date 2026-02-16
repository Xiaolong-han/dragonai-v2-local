from typing import TypedDict


class Skill(TypedDict):
    """A skill that can be progressively disclosed to the agent."""
    name: str
    description: str
    content: str


SKILLS: list[Skill] = [
    {
        "name": "image_generation",
        "description": "Generate images from text descriptions using the z-image-turbo or qwen-image model.",
        "content": """# Image Generation Skill

## Model Options
- **z-image-turbo**: Fast image generation for quick previews
- **qwen-image**: High-quality image generation for detailed results

## Usage Instructions
1. Describe the image you want to generate in detail
2. Specify the model preference if you have one
3. The skill will generate the image and return it

## Example Prompts
- "A cute cat sitting on a windowsill, sunset in background, watercolor style"
- "Futuristic cityscape at night, neon lights, cyberpunk aesthetic"
- "Professional product photo of a coffee mug on a wooden table"
""",
    },
    {
        "name": "image_editing",
        "description": "Edit existing images based on text instructions.",
        "content": """# Image Editing Skill

## Capabilities
- Modify existing images
- Apply filters and effects
- Change colors and styles
- Remove or add elements

## Usage Instructions
1. Provide the image you want to edit
2. Describe the changes you want in detail
3. The skill will apply the edits and return the modified image
""",
    },
    {
        "name": "coding",
        "description": "Write and debug code using specialized coding models.",
        "content": """# Coding Skill

## Model Options
- **qwen3-coder-flash**: Fast coding for quick solutions
- **qwen3-coder-plus**: Advanced coding for complex tasks

## Capabilities
- Write code in various programming languages
- Debug and fix existing code
- Explain code line by line
- Refactor and optimize code
- Generate unit tests

## Supported Languages
- Python
- JavaScript/TypeScript
- Java
- C/C++
- Go
- Rust
- And many more

## Usage Instructions
1. Describe your coding task clearly
2. Specify the programming language if needed
3. Choose between flash or plus model based on complexity
""",
    },
    {
        "name": "translation",
        "description": "Translate text between languages using specialized translation models.",
        "content": """# Translation Skill

## Model Options
- **qwen-mt-flash**: Fast translation for quick needs
- **qwen-mt-plus**: High-quality translation for professional results

## Supported Languages
- Chinese (Simplified/Traditional)
- English
- Japanese
- Korean
- Spanish
- French
- German
- And many more

## Usage Instructions
1. Provide the text you want to translate
2. Specify the source and target languages
3. Choose between flash or plus model based on quality needs

## Example
- Source: "Hello, world!"
- Target: "你好，世界！"
""",
    },
]
