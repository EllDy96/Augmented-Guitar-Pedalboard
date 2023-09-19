#  Augmented Guitar Pedalboards
## Introduction 
We proposed an innovative smart audio effect based on the conjunction of muscolar signals and deep learning analysis,  to introduce a novel interaction strategy into the world of guitarists. We investigated how to effectively adapt the guitar sound by dynamically tracking the user's musical intentions through an analysis of muscular contractions using wearable devices. To track musical intentions,  two Recurrent Neural Networks based on Bidirectional Long-Short Term Memory (BLSTM)  has been developed to interpret surface electromyography signals.  To train the system the  musicians  provide  their  gestural  vocabulary, each  associated with a pedalboard's sonic preset; We collected from multiple  musicians various sEMG acquisitions  (related to  popular  guitar  techniques) in order  to create  a training dataset; it is available to support similar applications. The  digital  signal processing is carried  out with Max 8, where we define the digital pedalboard. The goal of this  work is to help other researchers integrate muscle signals into artistic performance by proposing a protocol for mapping sEMG with sound.

## Problem formulation 
![Probem formulation](/introductiveImages/problemFormulation.png)
We proposed a protocol to incorporate guitarists' gestures into the interaction procedure, allowing guitarists to interact with their effects no longer with their feet but by performing a predefined set of techniques (such as fingerpicking, tapping, strumming...); in this way, it is no longer the press of a bottom to trigger one pedalboard preset but the performing of a technique. 

For a detailed explanation please read the [scientific paper](/article/Thesis___DavideLionetti.pdf) or the [Executive Summary](/article/Executive_Summary_DavideLionetti.pdf)
## Intra-subject Dataset
![Dataset Creation](/introductiveImages/dataset__creation.png)
For the training process, we defined a systematic and scalable procedure, put into practice on four guitarists.
The proposed  tool is intra-subject, meaning  that it is built  upon the stylistic  decision of the user, that train  it. For this reason, we define a procedural approach to train  the system.  The dataset was meticulously  constructed following a strict  procedure:

1.  Seven guitar  techniques  were selected namely:  fingerpicking, strumming, bending, down picking, alternate picking, tapping,  and pull-off/hammer-on.
2.  Each  technique  was  paired  with  a  corresponding   guitar  riff 3   that best  represented its  characteristic
motion,  to ensure consistent movements  across different participants,
3.  Two acquisitions  were performed  for each technique, asking the tester  to play at different levels of muscle contraction, in order  to  detect  the  maximum  and  minimum  contraction to  train  the  regression  mode, which aims to differentiate the varying  levels of force exerted  during  the gestures.
4.  Each acquisition  was performed  with the same electric guitar  in a standing  position,  with a fixed duration
(30 s) and a constant tempo  of 100 beats  per minute  (BPM).
5.  Finally,  a built-in  function  within the company's acquisition software was utilized to export  a filtered RMS version of each acqui- sition,  saving the maximum  and the minimum  values for each muscles to apply  a normalization between [0, 1].

The data was collected from four guitarists (both  male and female) with varying levels of expertise,  spanning from beginner  to professional,  and  with  diverse anthropometric measures  such as heights,  weights,  and  muscle shapes, all carefully documented in [guitar gesture sEMG Dataset](https://github.com/EllDy96/Augmented-Guitar-Pedalboard/tree/main/dataset).

### How to use it
The system is written using Python 3.10.8 and Tensorflow 2 within a Conda environment, please install the dependencies using the [environment file](/anacondaRequirements/environment.yml).
