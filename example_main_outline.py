import asyncio
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineTask
from pipecat.pipeline.pipeline import Pipeline
from pipecat.frames import TextFrame
from my_custom_services import WakeWordDetectionService, ImageToTextService, AudioToTextService, InsultTextService, TTSService, PlaySpeechService

# Initialize services
wake_word_service = WakeWordDetectionService()
image_to_text_service = ImageToTextService(api_key='GEMINI_API_KEY')
audio_to_text_service = AudioToTextService(api_key='GEMINI_API_KEY')
insult_service = InsultTextService(api_key='GEMINI_API_KEY')  # Service to generate insult text
tts_service = TTSService(api_key='CARTESIA_API_KEY')
play_speech_service = PlaySpeechService()  # Plays the generated speech

# Runner to manage multiple tasks
runner = PipelineRunner()

# Event handler for wake word detection
async def on_wake_word_detected():
    # 1. Capture image and process it to text (Pipe 1)
    #12a video flash example, swap in local transport and add deepgram element in transport (requires deepgram api key)
    # OR ....
    # Just see if you can get the local transport working and it will work for us, just write a little wrapper as a pipecat service
    # self.pushframe 
    # 
    image_task = PipelineTask(Pipeline([image_to_text_service]))
    await runner.run(image_task)
    image_text_frame = image_task.get_result()  # Resulting text from image

    # 2. Record audio and process it to text (Pipe 2)
    audio_task = PipelineTask(Pipeline([audio_to_text_service]))
    await runner.run(audio_task)
    audio_text_frame = audio_task.get_result()  # Resulting text from audio

    # 3. Combine text from image and audio
    combined_text = image_text_frame.data + " " + audio_text_frame.data
    combined_text_frame = TextFrame(data=combined_text)
    
    # 3.1 Send combined text to Gemini for insult generation (Pipe 3)
    insult_task = PipelineTask(Pipeline([insult_service]))
    await insult_task.process(combined_text_frame)  # Send combined text for insult generation
    await runner.run(insult_task)
    insult_text_frame = insult_task.get_result()  # Get the insult text

    # 4. Send the insult text to Cartesia TTS to generate speech (Pipe 4)
    tts_task = PipelineTask(Pipeline([tts_service]))
    await tts_task.process(insult_text_frame)
    await runner.run(tts_task)

    # 5. Play the generated speech
    speech_frame = tts_task.get_result()  # The resulting audio frame (speech)
    await play_speech_service.play(speech_frame)

# Main loop to listen for the wake word and trigger the process
async def main():
    while True:
        if await wake_word_service.listen_for_wake_word():  # Blocking call until wake word detected
            await on_wake_word_detected()

# Run the main loop
if __name__ == "__main__":
    asyncio.run(main())
