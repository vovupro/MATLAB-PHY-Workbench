# MATLAB PHY Workbench — Level 0

Desktop block-diagram debugger with MATLAB as the sole signal-processing and plotting engine.

## Interaction

- Mouse wheel: zoom the system diagram
- Drag empty canvas: pan
- `+` / `−`: expand or collapse a major block
- Click a child calculation: select it and show its editable note
- Click **Update note** to persist the note for that node
- Click **Plot in MATLAB** only when an input/output figure is needed

## System map

The canvas shows the complete intended link-level architecture:

`Source → TX Coding → TX Waveform → Channel → RX Waveform → RX Decoding → Metrics`

An `Adaptation` feedback loop returns CSI/CQI/ACK information and controls MCS and receiver complexity. Level 0 MATLAB plots are currently active for source bits, grouping, M-QAM, AWGN, detection, and BER. The remaining 5G/OFDM/LDPC/adaptation nodes are placed in their final architectural positions for incremental implementation.

MATLAB saves a complete `trace.mat`; the GUI does not duplicate plot rendering. This keeps the interface light and makes later levels additive: new blocks are described in the Python graph model and implemented as MATLAB functions.

## Requirements

- Windows
- MATLAB registered as a COM Automation server (verified with R2023a on this machine)
- Python 3.11
- PySide6 and pywin32

Double-click `run_app.bat`. The app attaches to MATLAB Desktop, or starts it if necessary, and reuses that session. Closing the app intentionally leaves MATLAB and its native figures open for further debugging.

## Project layout

- `matlab/phy_level0_run.m`: complete Level 0 calculation
- `matlab/phy_render_trace.m`: MATLAB-owned input/output plots
- `phy_workbench/diagram.py`: zoomable, hierarchical block diagram
- `phy_workbench/matlab_bridge.py`: persistent MATLAB COM worker
- `phy_workbench/main_window.py`: controls and figure inspector
