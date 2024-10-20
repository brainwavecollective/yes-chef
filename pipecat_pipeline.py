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
        try:
            self.porcupine = Porcupine(access_key="your_picovoice_key", keywords=["Hey Chef"])
        except Exception as e:
            print(f"Failed to initialize Porcupine: {e}")

    async def process(self, frame, context):
        try:
            print("Listening for wake word...")
            keyword_index = self.porcupine.process(frame.audio)
            if keyword_index >= 0:
                print("Wake word detected!")
                return frame
        except Exception as e:
            print(f"Error processing audio frame: {e}")
        return None  # Continue listening if no wake word is detected

    def cleanup(self):
        if self.porcupine:
            self.porcupine.delete()

# Custom processor for camera capture
class CameraCaptureProcessor:
    def __init__(self):
        self.camera = CameraModule()

    async def process(self, frame, context):
        print("Capturing image...")
        try:
            image = self.camera.capture_image()  # Capture image
            if image is None:
                raise RuntimeError("Failed to capture image.")
            frame["image"] = image
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None  # Handle failure gracefully
        return frame

# Custom processor for Gemini analysis
class GeminiPhotoAnalysisProcessor:
    async def process(self, frame, context):
        try:
            print("Analyzing photo with Gemini...")
            image = frame.get("image")
            if image is None:
                raise ValueError("No image found in the frame!")
            description = await gemini_chat(image)  # Await if async
            frame["description"] = description
        except Exception as e:
            print(f"Error in Gemini photo analysis: {e}")
            return None
        return frame

# Custom processor for Cartesia TTS service
class CartesiaTTSProcessor:
    def __init__(self, tts_service):
        self.tts_service = tts_service

    async def process(self, frame, context):
        try:
            print("Converting description to speech with Cartesia...")
            description = frame.get("description")
            if description is None:
                raise ValueError("No description found in the frame!")
            tts_result = await self.tts_service.generate_tts(description)
            frame["tts_audio"] = tts_result.audio  # Assuming `audio` is the correct attribute
            frame["tts_duration"] = tts_result.duration  # Assuming the TTS service returns duration
        except Exception as e:
            print(f"Error in Cartesia TTS: {e}")
            return None
        return frame

# Custom processor for mouth movement synchronization
class ServoMouthSyncProcessor:
    def __init__(self):
        self.puppet_control = ChefPuppetControl()

    async def process(self, frame, context):
        try:
            print("Synchronizing mouth movement with TTS...")
            tts_duration = frame.get("tts_duration")
            if tts_duration is None:
                raise ValueError("No TTS duration found in the frame!")
            # Sync the mouth movement to match the TTS duration
            self.puppet_control.sync_mouth(tts_duration)
        except Exception as e:
            print(f"Error in mouth sync: {e}")
        return frame

# Main function to set up and run the pipeline
async def main():
    # Set up Cartesia for text-to-speech
    tts_service = CartesiaTTSService(api_key="your_cartesia_api_key", voice_id="your_voice_id")
    tts_processor = CartesiaTTSProcessor(tts_service)

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
        tts_processor,          # Step 4: Convert Gemini text to speech
        servo_processor         # Step 5: Sync puppet mouth with TTS
    ])

    # Create a task to run the pipeline
    runner = PipelineRunner()
    task = PipelineTask(pipeline)
    
    # Start the pipeline runner
    try:
        await runner.run(task)
    except Exception as e:
        print(f"Pipeline failed: {e}")
    finally:
        # Cleanup resources
        wake_word_processor.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
