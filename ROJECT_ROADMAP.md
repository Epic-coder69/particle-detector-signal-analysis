# Project Roadmap

## 1. Purpose

This project studies relationships between energetic-particle populations
and magnetic-field structures in space plasma using real experimental data.

The goals are to:

- learn experimental and computational plasma physics
- develop a reproducible scientific-analysis workflow
- work toward genuine research questions

## 2. Scientific Direction

Main question:

How are energetic-particle populations related to magnetic-field structures
and magnetic variability in space plasma?

Initial questions include:

- Do energetic-particle enhancements coincide with changes in the magnetic field?
- Do different particle energies respond differently?
- Are particle enhancements associated with magnetic rotations, switchbacks,
  turbulence, or other plasma structures?
- Can these relationships be distinguished from random coincidence?

If relationships are found, possible physical explanations may include:

- particle acceleration
- particle transport
- magnetic connectivity
- turbulence
- common plasma or solar structures

Correlation will not automatically be interpreted as evidence of local
particle acceleration.

Novelty is a goal, not an assumption.


## 3. Experimental Data

The current analysis uses Parker Solar Probe measurements.

Primary instruments:

- FIELDS — magnetic-field measurements
- IS☉IS — energetic-particle measurements and energy-dependent flux

## 4. Analysis Strategy

The project follows this general progression:

1. Understand the instruments, measurements, units, cadence, and data quality.
2. Identify useful particle-rich and reference intervals.
3. Clean, synchronize, and visualize magnetic-field and particle measurements.
4. Examine particle behavior as a function of energy and time.
5. Quantify magnetic-field variability and directional changes.
6. Identify magnetic structures such as rotations and candidate switchbacks.
7. Compare particle populations before, during, and after those structures.
8. Test whether observed relationships are statistically significant.
9. Compare multiple events and control intervals.
10. Interpret significant results physically.


## 5. Current Stage

The initial Parker Solar Probe data pipeline is working.

So far the project has:

- loaded and inspected real NASA CDF data
- verified measurement cadence and data coverage
- distinguished valid zero-count measurements from missing data
- analyzed FIELDS magnetic-field measurements
- analyzed IS☉IS proton measurements
- identified a particle-rich interval on 2018-11-17
- compared it with a lower-activity interval on 2018-11-06
- produced synchronized magnetic-field and proton-activity plots
- produced an energy-resolved proton-flux spectrogram

The next step is to move from visual comparison to quantitative
particle-field analysis.


## 6. What Success Looks Like

A successful project should produce:

- a reproducible analysis pipeline
- scientifically justified data handling
- quantitative particle-field comparisons
- uncertainty estimates and statistical controls
- clear scientific figures
- documented Python code
- a research-style interpretation of the results

A successful project does not require discovering new physics.

Reproducing known behavior, testing a hypothesis rigorously, finding a
statistically significant relationship, or obtaining a well-supported null
result are all valid scientific outcomes.

If the analysis reveals a potentially new relationship, it can become the
basis for deeper research.
