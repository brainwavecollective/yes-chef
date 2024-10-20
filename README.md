# yes-chef

Yes Chef! provides everything you need to run a multimodal animatronic robot capable of responding to your voice commands. Although some aspects rely on readily available products and services, this project overwhelmingly builds upon on Open Source efforts, to include the robotic arm itself. 

**WARNING**: Our robot may be cute, but he is not suitable for children. As presented this will create a robot that is extremely foul mouthed and will mercilessly insult you. His words cut deep. You have been warned.  

# Hardware 

While this effort is focused on the SO-ARM100 v1.2, there is no reason why any other Open Source robotic arm could not be used, albeit with minor modifications. Our results can be entirely reproduced using only a follower arm, so the leader arm can be ignored for this project.  The following is required:  

 - Robotic Arm (e.g., SO-ARM100 v1.2)
 - A server (laptop, Raspberry Pi, etc.)
 - Webcam (to see what Chef is going to be insulting)
 - Microphone (ours includes a webcam)
 - A Speaker (for all audio)

# Hardware Configuration 

This entire project was inspired by, and would not have been possible without HuggingFace's incredible LeRobot. LeRobot includes scripts to help you setup your servos during the build process, as well as identify things on your host like port configurations. Additionally, the related libraries greatly simplify interactions. In short, without LeRobot we wouldn't have been able to enable the overwhelming majority of the functionality that you see here.  

**IMPORTANT!!!*  

A lot of the configuration that we have in place expects that you will have appropriately setup and configured your robotic arm. Generally speaking, the steps for this vary greatly, but in this case, there may be additional considerations for your specific robotic arm and and potential puppet that you have in place as well. In short, please be diligent to ensure that you have performed all necessary steps *for your particular implementation*  

# Environment Setup
After your robot is built, it will need to be connected to your server VIA USB. While you can use a laptop for this, we used a Raspberry Pi.  

Once connected to your server, with all necessary hardware configured and correct mapped out, you will need to bring down a specific branch of LeRobot to ensure that you have the latest info. Note: this is expected to be updated to the main branch soon `pip install git+ssh://git@github.com/huggingface/lerobot.git@user/rcadene/2024_09_04_feetech`  

Then run `pip install -r requirements.txt` to install dependenceis for this project.

## Configurable Settings 

### Response Prompt 
Ours is crafted to produce a specific type of insulting response, but you can modify this to suit your own needs.

### Wake & Sleep Positions 
We used a script that we created (and intend to submit to LeRobot) which records current positions of the robot for future use. Specifically, we held the arm in the position that we wanted, once for "slumped over and sleeping" and another for "awak and on a rampage."  As you can imagine, these positions are specific to the puppet that we used, and will vary based on the avatar that you use.

### Input Voice 
Cartesia offers the ability to use a multitude of voices, including ones that you train using your own voice. In short, your robot can sound like anything that you would want it to.

### Background Music 
We support a number of background music options. These are randomly selected for each run, but you will need to upload the music of your choice. We used Suno to generate ours.

### Wake Word 
This is the phrase that will cause the robot to come alive.  

# Operating the Robot 
## Step 1: Run the service : `python main.py`
## Step 2: Say the wake word "Hello Chef!"
## Step 3: Get Roasted 

Enjoy. We sure had fun with this one!  

