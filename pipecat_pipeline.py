
import asyncio
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.cartesia import CartesiaTTSService
from camera_module import CameraModule
from ImageDescription import gemini_chat
from chef_puppet_control import ChefPuppetControl
from pvporcupine import Porcupine

# Custom processor for wake word detection
class WakeWordProcessor:
    def __init__(self):
        self.porcupine = Porcupine(access_key="your_picovoice_key", keywords=["Hey Chef"])

    async def process(self, frame, context):
        print("Listening for wake word...")
        # Process audio and check for wake word
        keyword_index = self.porcupine.process(frame.audio)
        if keyword_index >= 0:
            print("Wake word detected!")
            return frame  # Proceed to next processor
        return None  # Continue listening if no wake word is detected

# Custom processor for camera capture
class CameraCaptureProcessor:
    def __init__(self):
        self.camera = CameraModule()

    async def process(self, frame, context):
        print("Capturing image...")
        image = self.camera.capture_image()  # Take the photo
        frame["image"] = image  # Pass the image to the next processor
        return frame

# Custom processor for Gemini analysis
class GeminiPhotoAnalysisProcessor:
    async def process(self, frame, context):
        print("Analyzing photo with Gemini...")
        image = frame.get("image")
        if image is None:
            raise ValueError("No image found in the frame!")
        description = gemini_chat(image)  # Send the image to Gemini
        frame["description"] = description  # Pass the description to TTS processor
        return frame

# Custom processor for mouth movement synchronization
class ServoMouthSyncProcessor:
    def __init__(self):
        self.puppet_control = ChefPuppetControl()

    async def process(self, frame, context):
        print("Synchronizing mouth movement with TTS...")
        tts_duration = frame.get("tts_duration")
        if tts_duration is None:
            raise ValueError("No TTS duration found in the frame!")
        # Sync the mouth movement to match the TTS duration
        self.puppet_control.sync_mouth(tts_duration)
        return frame

# Main function to set up and run the pipeline
async def main():
    # Set up Cartesia for text-to-speech
    tts_service = CartesiaTTSService(api_key="your_cartesia_api_key", voice_id="your_voice_id")

    # Create processors for each step
    wake_word_processor = WakeWordProcessor()
    camera_processor = CameraCaptureProcessor()
    gemini_processor = GeminiPhotoAnalysisProcessor()
    servo_processor = ServoMouthSyncProcessor()

    # Create the Pipecat pipeline with all processors
    pipeline = Pipeline([
        wake_word_processor,    # Step 1: Wake word detection
        camera_processor,       # Step 2: Capture image
        gemini_processor,       # Step 3: Analyze image with Gemini
        tts_service,            # Step 4: Convert Gemini text to speech
        servo_processor         # Step 5: Sync puppet mouth with TTS
    ])

    # Create a task to run the pipeline
    runner = PipelineRunner()
    task = PipelineTask(pipeline)
    
    # Start the pipeline runner
    await runner.run(task)

if __name__ == "__main__":
    asyncio.run(main())
