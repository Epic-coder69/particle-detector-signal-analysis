# Project Roadmap

## 1. Purpose
Why I am doing this project:
- learn experimental/computational plasma physics
- work toward genuine research
- build a strong scientific-computing portfolio for student jobs

## 2. Scientific Direction
Study the relationship between energetic particles and magnetic-field
structures in the near-Sun plasma using Parker Solar Probe data.

Initial question:
Are energetic-particle enhancements associated with magnetic switchbacks
or other magnetic structures?

The project may later investigate whether observed relationships are better
explained by particle acceleration, transport, magnetic connectivity, or
other plasma processes.

Novelty is a goal, not an assumption.

## 3. Data
Primary measurements:

- IS☉IS — energetic particles and their energy-dependent flux
- FIELDS — magnetic-field measurements

Possible later addition:
- SWEAP — bulk solar-wind plasma measurements

Parker Solar Probe is the initial focus, but methods may later be applied
to other plasma/particle datasets.

## 4. Approach
1. Learn the relevant physics and understand the measurements.
2. Start working with a small amount of real Parker data.
3. Clean, synchronize, and visualize the measurements.
4. Develop reliable event-detection methods.
5. Identify magnetic structures such as switchbacks.
6. Compare particle behavior around those structures.
7. Test whether relationships are stronger than random coincidence.
8. Interpret interesting results physically.

Synthetic data will remain useful for testing and validation, but real
spacecraft data is the main project.

## 5. What Success Looks Like
The project should eventually produce:

- a working and reproducible scientific-analysis pipeline
- analysis of real Parker Solar Probe measurements
- quantitative results with uncertainties and statistical controls
- clear scientific figures
- documented code on GitHub
- a research-style explanation/report of the method and results

A successful project does not require discovering new physics.
Reproducing known results, testing hypotheses rigorously, or obtaining a
well-supported null result are all valid outcomes.

If the analysis reveals a potentially new relationship, it can become the
basis for deeper research.

## 6. Current Status and Next Steps
Already completed:
- synthetic detector-signal simulation
- noise and SNR studies
- event detection
- pulse reconstruction
- Monte Carlo performance studies
- Git/GitHub setup

Next:
1. finish this roadmap
2. understand the relevant Parker instruments/data products
3. obtain a small real IS☉IS/FIELDS dataset
4. make our first real-data plots
5. decide the first concrete analysis from what we learn
