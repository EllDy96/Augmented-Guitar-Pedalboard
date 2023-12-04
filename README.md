# Augmented Guitar Pedalboard

Welcome to the Augmented Guitar Pedalboard repository! 🎸🔊

## Overview

Explore the future of musical interaction with our innovative smart audio effect that combines muscular signals and deep learning analysis. We aim to revolutionize the guitarist's experience by introducing a novel interaction strategy into their world.

## Key Features

- **Muscular Signal Analysis:** Dynamically adapt the guitar sound by tracking the user's musical intentions through the analysis of muscular contractions using wearable devices.

- **Deep Learning with BLSTM:** Two Recurrent Neural Networks based on Bidirectional Long-Short Term Memory (BLSTM) have been developed to interpret surface electromyography signals, providing a nuanced understanding of the musician's gestures.

- **User-Defined Gestural Vocabulary:** Musicians can train the system by providing their gestural vocabulary, each associated with a specific pedalboard sonic preset.

- **Rich Training Dataset:** We've collected diverse surface electromyography (sEMG) acquisitions from multiple musicians, covering popular guitar techniques. The resulting training dataset is available to support similar applications.

- **Max 8 Integration:** Digital signal processing is seamlessly executed with Max 8, where the digital pedalboard is defined.

## Getting Started

To embark on your journey with the Augmented Guitar Pedalboard, follow these steps:

1. **Clone the Repository:** `git clone https://github.com/your-username/augmented-guitar-pedalboard.git`
2. **Install Dependencies:** The system is written using Python 3.10.8 and Tensorflow 2 within a Conda environment, please create a Conda environment using the dependencies listed in the [environment file](/anacondaRequirements/environment_augmentedPedalboard.yml).
3. **Explore the Code:** Dive into the codebase and discover the magic behind our innovative audio effect. You will need Max 8 and an IDE such as Visual Studio Code. 

## Usage

- Customize your pedalboard's sonic presets based on your unique gestural vocabulary.
- Experiment with the integration of muscle signals into your artistic performances.
## How It Works

### Problem Formulation

![Problem Formulation](/introductiveImages/problemFormulation.png)

We've addressed a fundamental challenge in guitar effects interaction by proposing a protocol that seamlessly incorporates guitarists' gestures into the interaction procedure. This innovative approach allows guitarists to engage with their effects not through foot pedals but by performing a predefined set of techniques, such as fingerpicking, tapping, strumming, and more. With this paradigm shift, triggering a pedalboard preset is no longer a mere button press but an expressive act of technique execution.

For a detailed exploration, please refer to the [scientific paper](/article/Thesis___DavideLionetti.pdf) or the [Executive Summary](/article/Executive_Summary_DavideLionetti.pdf).

### Intra-subject Dataset

![Dataset Creation](/introductiveImages/dataset__creation.png)

To train the system effectively, we implemented a systematic and scalable procedure, demonstrated through practical application on four guitarists. Our proposed tool is intra-subject, meaning it is crafted based on the stylistic decisions of the user who trains it. Consequently, we've defined a procedural approach to train the system, and the dataset construction followed a meticulous procedure:

1. **Selection of Techniques:** Seven guitar techniques were meticulously chosen, covering a spectrum from fingerpicking and strumming to bending, down picking, alternate picking, tapping, and pull-off/hammer-on.

2. **Technique-Riff Pairing:** Each technique was paired with a corresponding guitar riff to best represent its characteristic motion. This pairing ensures consistent movements across different participants.

3. **Muscle Contraction Levels:** Two acquisitions were performed for each technique, with testers playing at different levels of muscle contraction. This diversity helps detect the maximum and minimum contraction levels necessary to train the regression model, differentiating varying force levels during gestures.

4. **Acquisition Setup:** Each acquisition was executed with the same electric guitar in a standing position, maintaining a fixed duration (30 s) and a constant tempo of 100 beats per minute (BPM).

5. **RMS Filtering and Normalization:** A built-in function within the acquisition software exported a filtered RMS version of each acquisition, saving maximum and minimum values for each muscle. This information was crucial for applying normalization between [0, 1].

The dataset was meticulously collected from four guitarists, encompassing a diverse range of expertise levels, gender representation, and anthropometric measures such as heights, weights, and muscle shapes. For detailed documentation, refer to the [Guitar Gesture sEMG Dataset](https://github.com/EllDy96/Augmented-Guitar-Pedalboard/tree/main/dataset).


## About
The Augmented Guitar Pedalboard project has been developed for my M.Sc final thesis in Music Engineering at Politecnico di Milano during an internship at [LWT3](https://lwt3.com/). it is driven by my passion for pushing the boundaries of musical expression. Join me on this journey as we explore the integration of muscle signals into artistic performance.

## Contributing

We welcome contributions from the community! Whether you're passionate about signal processing, deep learning, or musical innovation, your expertise is valuable. Check out our [contribution guidelines](CONTRIBUTING.md) to get started.


## Acknowledgments
I want to thank  all the  LWT3  members  for being like a second house for me during  my internship while I was developing  this  project, especially Paolo  Belluco for the  continuous  support and  all the  vital  advices,  Samuele Polistina for the Max/MSP support, Luigi Attoresi  for the tailoring  work to my torn  pants,  Roberto  Alessandri for being the best fellow artist friend I could imagine.  I also want to thank  Giusy Caruso,  who inspired me a lot and strengthened my dream  of becoming an artistic researcher,  I will become like you one-day Giusy.  I want to thank  my professor Massimiliano  Zanoni  for the  brilliant knowledge that he gave to me during  his course and the support for this project,  I am very grateful  to him for reminding  me that you can also be an artist being a programmer.

I extend our gratitude to the open-source community and fellow musicians for their support and inspiration.



Happy coding and happy playing! 🎶🤘



