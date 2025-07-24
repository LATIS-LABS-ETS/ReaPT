# ReaPT: Realtime Palate Tracker

## Overview

**ReaPT** (**Rea**ltime **P**alate **T**racker) is a transparent application designed to overlay ultrasound software like EchoWave for real-time biofeedback and intervention. It allows clinicians and researchers to trace, track, and annotate the palate's position during speech or swallowing tasks.

## Getting Started

When you launch ReaPT, you are presented with the main screen where you configure the session.

### 1. Select Mode

You must first choose one of two primary modes:

* **Process Videos**: Select this mode if you have ultrasound video files that need to be processed to automatically generate a palate trace.
* **Draw Traces (or Import CSV)**: Select this mode to manually draw a new palate trace, or to import a pre-existing trace from a `.csv` file.
  
<img width="442" height="541" alt="image" src="https://github.com/user-attachments/assets/5035abb4-b28f-4d61-bb41-095dd8704e97" /><img width="443" height="543" alt="image" src="https://github.com/user-attachments/assets/3fd2ca47-040b-448d-ba7a-fa7978afdf4a" />
### 2. Add Participants

For each participant, you need to provide their data:

* In **Process Videos** mode, click **Browse** to select the participant's video file.
* In **Draw Traces / Import CSV** mode, you can either click **Browse** to select a `.csv` file containing a palate trace, or simply type a participant matching key (e.g., "145") into the text field if you plan to draw the trace manually.


You can add multiple participants to a single session by clicking **Add Participant**. This will create a new input field for the next participant's data.

<img width="461" height="563" alt="image" src="https://github.com/user-attachments/assets/41767ceb-7c30-43af-a8b4-d6334d1493bb" /><img width="457" height="562" alt="image" src="https://github.com/user-attachments/assets/e0ea2efa-db41-46f8-a349-0552783be1b8" />



### 3. Start the Session

* Choose which participant to start the session with.
* Click the **Start** button.
    * In **Process Videos** mode, ReaPT will begin processing the video files. A loading screen will show the progress.
      
      <img width="448" height="553" alt="image" src="https://github.com/user-attachments/assets/caa7c288-f6e3-4eee-b558-b1517cc12ec9" /><img width="451" height="553" alt="image" src="https://github.com/user-attachments/assets/36278b1b-91d6-413f-a494-fc35447c4bba" />


    * In **Draw Traces / Import CSV** mode, the transparent overlay will launch immediately.

## Using the Transparent Overlay

The overlay is where all the real-time interaction happens. It appears as a transparent window over your primary ultrasound software.

<img width="975" height="548" alt="image" src="https://github.com/user-attachments/assets/bd3d818d-9021-45ab-9af3-169acee28c91" />

### Palate Repositioning 

The initial palate trace (yellow line) is based on the automatically processed video or the imported file. Its shape will be correct, but its position on the screen may need to be adjusted to align with the live ultrasound image.

To reposition the trace:

1.  Have the participant press their tongue against their hard palate to make it clearly visible in the ultrasound feed.
2.  Manually draw an **alignment line** (blue) over the visible palate in the ultrasound image.
   
<img width="975" height="548" alt="image" src="https://github.com/user-attachments/assets/1e980074-9a2d-4613-978e-58e39ed2b592" />

4.  Press the **Enter** key. The yellow palate trace will instantly snap to the position and rotation of the alignment line you just drew.
5.  This process must be repeated any time the participant moves or the ultrasound probe is shifted, causing the palate to move on the screen.
   
<img width="975" height="548" alt="image" src="https://github.com/user-attachments/assets/bfc645b0-31b3-4387-9460-83ae5e568184" />

### Manual Palate Tracing

If you start in "Draw Traces" mode without importing a file, the overlay will be empty. You can draw the palate shape. Once you are satisfied, press **P** to save the trace as a `.csv` file for future use.
### Annotation Mode

You can draw annotations directly on the overlay to provide visual cues or highlight specific structures.

* **Drawing**: Simply draw on the screen. The application interprets most drawing as an **annotation** (red line).
  
  <img width="975" height="548" alt="image" src="https://github.com/user-attachments/assets/a5135679-ca02-4c6d-b041-5046c7b88e13" />
* **Distinguishing from Alignment**: The app is programmed to interpret a clear horizontal line drawn from right to left as an alignment line for repositioning. Other shapes are treated as annotations.
* **Clearing**: Annotations can be cleared by pressing the **Del** key or a configured key on an XP Pen pad .
* **Movement**: When you reposition the palate trace, any annotations you have drawn will move along with it, maintaining their position relative to the palate.
  
<img width="975" height="548" alt="image" src="https://github.com/user-attachments/assets/eddcb16b-9cac-4ebe-8300-fe057da9740b" />




## Multi-Participant Use

### Switching Between Participants

If you loaded multiple participants at the start of the session, you can quickly switch between their palate traces.

* Press the keyboard number corresponding to the participant's import order (e.g., **1** for the first participant, **2** for the second, and so on).
* The active participant's matching key will be displayed in the top-right corner of the screen.

<img width="981" height="553" alt="image" src="https://github.com/user-attachments/assets/b6c3fc54-c68d-4975-88ff-df35a9f7dd6c" />

## Warnings and Key Considerations

* **Processing Time**: Video processing can be time-consuming. To save time, it's recommended to have participants perform dry swallows during intake recordings so palate traces can be generated before the intervention session.
* **Accuracy**: Automatically generated palate traces may sometimes be incomplete or inaccurate. Always verify the trace against the live ultrasound.
* **Minimize Movement**: Using a microphone stand or other stabilization equipment for the ultrasound probe during sessions can minimize movement, reducing the need for frequent repositioning of the palate trace.

## Color Key

* **Yellow Line**: The main palate trace.
* **Blue Line**: The temporary alignment line you draw for repositioning.
* **Red Line**: Annotations.
