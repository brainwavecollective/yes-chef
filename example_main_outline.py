import asyncio
from pipecat.frames import TextFrame, ImageFrame, AudioFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.runner import PipelineRunner
from my_custom_services import ImageToTextService, CartesiaTTSService, PlaySpeechService

# Initialize services
image_to_text_service = ImageToTextService(api_key='GEMINI_API_KEY')
tts_service = CartesiaTTSService(api_key='CARTESIA_API_KEY', voice_id='your-voice-id')
play_speech_service = PlaySpeechService()

# Runner to manage tasks
runner = PipelineRunner()

# Function to link the pipelines
async def process_image_to_speech():
    # Step 1: Pipeline 1 - Process the image and convert to text
    image_frame = ImageFrame(data="image data")  # Simulated image frame
    image_pipeline = Pipeline([image_to_text_service])
    image_task = PipelineTask(image_pipeline)
    
    # Run the first pipeline and get the output (TextFrame)
    await runner.run(image_task)
    text_frame = image_task.result  # Capture the output (text frame)

    # Step 2: Pipeline 2 - Take the text and convert it to speech using run_tts
    async for tts_frame in tts_service.run_tts(text_frame.data):
        if isinstance(tts_frame, AudioFrame):
            await play_speech_service.play(tts_frame)  # Play the generated audio
        elif isinstance(tts_frame, TTSStoppedFrame):
            break  # Stop when the TTS process is done

# Main event loop to start the process
async def main():
    await process_image_to_speech()

if __name__ == "__main__":
    asyncio.run(main())
