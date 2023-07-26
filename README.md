#  Augmented Guitar Pedalboards
## Introduction 
The proposed augmented musical instrument is based on the conjunction of electromyographic signals and deep learning analysis,  to introduce a novel interaction strategy into the world of guitarists. We investigated how to effectively adapt the guitar sound by dynamically tracking the user's musical intentions through an analysis of muscular contractions using wearable devices. To track musical intentions,  two Recurrent Neural Networks based on Bidirectional Long-Short Term Memory (BLSTM)  has been developed to interpret surface electromyography signals.  To train the system the  musicians  provide  their  gestural  vocabulary, each  associated with a pedalboard's sonic preset; We collected from multiple  musicians various sEMG acquisitions  (related to  popular  guitar  techniques) in order  to  create  a training dataset; it is available to support similar applications. The  digital  signal processing is carried  out with Max 8, where we define the digital pedalboard. The goal of this  work is to help other researchers integrate muscle signals into artistic performance by proposing a protocol for mapping sEMG with sound.

## Problem formulation 
![Uploading image.png…]()

### How to use it
The system is written using Python 3.10.8 and Tensorflow 2 within a Conda environment, please install the dependencies using the [environment file](/anacondaRequirements/environment.yml).
