### Overview
This is an image captioner that utilizes the Google Gemini API to caption images with natural language captions. It is written in python. I made this to automate the captioning part of the LoRA training process.

<img width="596" height="978" alt="image" src="https://github.com/user-attachments/assets/a61a0557-57c2-4db6-9691-e9266b139654" />

### Functionality
This program will use the first Gemini API Key until the free tier usage limit has been exhausted for all models in the dropdown list, it will then move to the second key and use that until it is exhausted, so on and so forth until all images are captioned. You can caption a lot of images just with the free tier limit from three or four API keys. Get your own Gemini API key here https://aistudio.google.com/app/api-keys . This program will create a text file with the same name as the image for each image in a given folder. Captioning NSFW images work about 90% of the time with the new "gemini-3-flash-preview" model. Simply demand the model to be as explicit as you like in the prompt.

### How to Use
1. Create a Gemini API key from this link https://aistudio.google.com/app/api-keys
2. Insert each API key (one per line) into the "API Keys" section in the app.
3. Provide a path to the folder containing the images in the app.
4. You can leave the "System Instructions" section blank, I do all my prompting in the user prompt section.
5. You can use the default prompt to generate a pretty good caption, or provide a custom prompt that will better suit your needs.
6. Hit the "Start Captioning" button to caption your images.

### Dependencies
```
pip install google-generativeai pillow pyinstaller
```

### How to build an .exe yourself
```
pyinstaller --noconsole --onefile captioner_withUI.py
```

### Downloads
Download [here](https://github.com/tobiasgpeterson/Gemini-API-Image-Captioner-with-UI/releases/download/main/GeminiImageCaptioner_withUI.exe).
