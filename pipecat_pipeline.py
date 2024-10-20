import asyncio
import sys
import os
import pvporcupine
from pipecat.processors.frame_processor import FrameProcessor  # Import the required class

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask


# Mock services for local testing
class MockCameraModule:
    def capture_image(self):
        print("Mock: Capturing image...")
        return "mock_image_data"  # Simulating image data


class MockChefPuppetControl:
    def sync_mouth(self, duration):
        print(f"Mock: Syncing puppet mouth for {duration} seconds...")


class MockCartesiaTTSService:
    async def generate_tts(self, description):
        print(f"Mock: Converting '{description}' to speech...")
        return MockTTSResult(duration=2.5)  # Simulating 2.5 seconds of speech


class MockTTSResult:
    def __init__(self, duration):
        self.duration = duration
        self.audio = "mock_audio_data"


# Custom processor for wake word detection
class WakeWordProcessor(FrameProcessor):
    def __init__(self):
        super().__init__()
        print("Simulating Porcupine wake word detection setup...")

    async def process(self, frame, context):
        # Simulate wake word detection by returning a "wake word detected" result
        print("Simulating wake word detection...")
        frame["wake_word_detected"] = True  # Simulate that the wake word was detected
        return frame  # Return the modified frame to continue the pipeline

    def cleanup(self):
        print("Simulating cleanup...")

    def set_parent(self, parent):
        self.parent = parent


# Custom processor for camera capture
class CameraCaptureProcessor(FrameProcessor):
    def __init__(self, camera_module):
        super().__init__()
        self.camera = camera_module

    async def process(self, frame, context):
        print("Capturing image...")
        try:
            image = self.camera.capture_image()  # Capture mock image
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
            description = await self.mock_gemini_chat(image)  # Mock Gemini analysis
            frame["description"] = description
        except Exception as e:
            print(f"Error in Gemini photo analysis: {e}")
            return None
        return frame

    async def mock_gemini_chat(self, image):
        print(f"Mock: Analyzing image: {image}")
        return "mock_image_description"

    def set_parent(self, parent):
        self.parent = parent


# Custom processor for Cartesia TTS service
class CartesiaTTSProcessor(FrameProcessor):
    def __init__(self, tts_service):
        super().__init__()
        self.tts_service = tts_service

    async def process(self, frame, context):
        try:
            print("Converting description to speech with Cartesia...")
            description = frame.get("description")
            if description is None:
                raise ValueError("No description found in the frame!")
            tts_result = await self.tts_service.generate_tts(description)
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
    def __init__(self, puppet_control):
        super().__init__()
        self.puppet_control = puppet_control

    async def process(self, frame, context):
        try:
            print("Synchronizing mouth movement with TTS...")
            tts_duration = frame.get("tts_duration")
            if tts_duration is None:
                raise ValueError("No TTS duration found in the frame!")
            # Sync the mouth movement to match the TTS duration (mocked)
            self.puppet_control.sync_mouth(tts_duration)
        except Exception as e:
            print(f"Error in mouth sync: {e}")
        return frame

    def set_parent(self, parent):
        self.parent = parent


# Main function to set up and run the pipeline
async def main():
    # Use mock services for local testing
    camera_module = MockCameraModule()
    puppet_control = MockChefPuppetControl()
    tts_service = MockCartesiaTTSService()

    # Create processors for each step
    wake_word_processor = WakeWordProcessor()
    camera_processor = CameraCaptureProcessor(camera_module)
    gemini_processor = GeminiPhotoAnalysisProcessor()
    tts_processor = CartesiaTTSProcessor(tts_service)
    servo_processor = ServoMouthSyncProcessor(puppet_control)

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
