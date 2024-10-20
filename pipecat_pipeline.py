import asyncio
import sys
import os
import pvporcupine
from pipecat.processors.frame_processor import FrameProcessor  # Import the required class

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.services.cartesia import CartesiaTTSService  # Assuming you have a real Cartesia TTS service
from camera_module import CameraModule  # Assuming you have a real camera module
from ImageDescription import gemini_chat  # Real Gemini analysis service
from chef_puppet_control import ChefPuppetControl  # Real puppet control service


# Custom processor for wake word detection
class WakeWordProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        try:
            # Initialize Porcupine with a real access key and wake word model
            self.porcupine = pvporcupine.create(
                access_key="your_picovoice_access_key",  # Replace with your actual access key
                keywords=["porcupine"]  # Replace with the correct wake word or model
            )
        except Exception as e:
            print(f"Failed to initialize Porcupine: {e}")

    async def process(self, frame, context):
        try:
            print("Listening for wake word...")
            keyword_index = self.porcupine.process(frame.audio)
            if keyword_index >= 0:
                print("Wake word detected!")
                return frame  # Proceed to the next processor
        except Exception as e:
            print(f"Error processing audio frame: {e}")
        return None  # Continue listening if no wake word is detected

    def cleanup(self):
        if self.porcupine:
            self.porcupine.delete()

    def set_parent(self, parent):
        self.parent = parent


# Custom processor for camera capture
class CameraCaptureProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.camera = CameraModule()  # Use the real camera module

    async def process(self, frame, context):
        print("Capturing image...")
        try:
            image = self.camera.capture_image()  # Capture real image
            if image is None:
                raise RuntimeError("Failed to capture image.")
            frame["image"] = image
        except Exception as e:
            print(f"Error capturing image: {e}")
            return None  # Handle failure gracefully
        return frame

    def set_parent(self, parent):
        self.parent = parent


# Custom processor for Gemini analysis
class GeminiPhotoAnalysisProcessor(FrameProcessor):
    async def process(self, frame, context):
        try:
            print("Analyzing photo with Gemini...")
            image = frame.get("image")
            if image is None:
                raise ValueError("No image found in the frame!")
            description = await gemini_chat(image)  # Send image to the real Gemini service
            frame["description"] = description
        except Exception as e:
            print(f"Error in Gemini photo analysis: {e}")
            return None
        return frame

    def set_parent(self, parent):
        self.parent = parent


# Custom processor for Cartesia TTS service
class CartesiaTTSProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.tts_service = CartesiaTTSService(api_key="your_cartesia_api_key", voice_id="your_voice_id")  # Real Cartesia service

    async def process(self, frame, context):
        try:
            print("Converting description to speech with Cartesia...")
            description = frame.get("description")
            if description is None:
                raise ValueError("No description found in the frame!")
            tts_result = await self.tts_service.generate_tts(description)  # Use the real TTS service
            frame["tts_audio"] = tts_result.audio
            frame["tts_duration"] = tts_result.duration
        except Exception as e:
            print(f"Error in Cartesia TTS: {e}")
            return None
        return frame

    def set_parent(self, parent):
        self.parent = parent


# Custom processor for mouth movement synchronization
class ServoMouthSyncProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        self.puppet_control = ChefPuppetControl()  # Use the real puppet control service

    async def process(self, frame, context):
        try:
            print("Synchronizing mouth movement with TTS...")
            tts_duration = frame.get("tts_duration")
            if tts_duration is None:
                raise ValueError("No TTS duration found in the frame!")
            # Sync the mouth movement to match the TTS duration using the real puppet control
            self.puppet_control.sync_mouth(tts_duration)
        except Exception as e:
            print(f"Error in mouth sync: {e}")
        return frame

    def set_parent(self, parent):
        self.parent = parent


# Main function to set up and run the pipeline
async def main():
    # Create processors for each step
    wake_word_processor = WakeWordProcessor()        # Step 1: Wake word detection
    camera_processor = CameraCaptureProcessor()      # Step 2: Capture image
    gemini_processor = GeminiPhotoAnalysisProcessor()  # Step 3: Analyze image with Gemini
    tts_processor = CartesiaTTSProcessor()           # Step 4: Convert Gemini text to speech
    servo_processor = ServoMouthSyncProcessor()      # Step 5: Sync puppet mouth with TTS

    # Create the Pipecat pipeline with all processors
    pipeline = Pipeline([
        wake_word_processor,
        camera_processor,
        gemini_processor,
        tts_processor,
        servo_processor
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
