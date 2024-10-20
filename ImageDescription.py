
import os
import google.generativeai as genai
from PIL import Image
from google.api_core import exceptions, retry
from google.generativeai.types import HarmCategory, HarmBlockThreshold
import weave
from dotenv import load_dotenv
import tempfile

# Load environment variables from .env file
load_dotenv()  # This will read from your .env file

# Configure Gemini API using the API key from the environment variables
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Function to upload image to Gemini
def upload_to_gemini(pil_image, mime_type=None):
    # Create a temporary file for the image
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
        temp_filename = temp_file.name

    # Save the image in PNG format
    pil_image.save(temp_filename, format="PNG")

    try:
        # Upload the image file to Gemini
        file = genai.upload_file(temp_filename, mime_type=mime_type or "image/png")
        print(f"Uploaded file '{file.display_name}' as: {file.uri}")
        return file
    finally:
        # Clean up the temporary file
        os.unlink(temp_filename)

# Retry logic in case of resource exhaustion
@weave.op
@retry.Retry(predicate=retry.if_exception_type(exceptions.ResourceExhausted))
def gemini_chat(pil_image):
    gemini_file = upload_to_gemini(pil_image)
    print(gemini_file)

    # Set model generation parameters
    generation_config = {
        "temperature": 1.2,
        "top_p": 0.95,
        "top_k": 40,
        "max_output_tokens": 8192,
        "response_mime_type": "text/plain",
    }

    # Initialize the model
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash-002",  # You can change to another model if required
        generation_config=generation_config,
    )

    # Generate a response based on the image
    response = model.generate_content([
        """You are to provide a detailed description of the provided image. Descriptions should be clear, accurate, and most importantly should describe the appearance of the person or people in the image. Age, gender, appearance, clothing, body language, and any other salient details. The response should not contain any preamble or other commentary.""",
        gemini_file,
    ],
    safety_settings={
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH
    })
    
    return response.text

# Main execution
if __name__ == "__main__":
    # Load the image to analyze
    img = Image.open("taken_image.jpg")  # Replace with your image file path
    result = gemini_chat(img)
    print(result)
