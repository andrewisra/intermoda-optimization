# AI Highlight for Proposal

## What is being built?

We build an **AI-Based Intermodal Transit Synchronization System** for DKI Jakarta public transport. The system treats MRT, LRT, and KRL as fixed schedule anchors that cannot be interrupted. AI is used to predict non-rail arrival time, passenger density, and missed-connection risk. The optimizer then recommends feasible actions for flexible non-rail modes such as TransJakarta, Mikrotrans, feeder buses, and school buses.

## AI components

1. **ETA Delay Prediction Model**  
   Predicts non-rail arrival delay using route, stop, time, traffic level, rainfall, incident flag, passenger density, and scheduled travel time.

2. **Passenger Density Prediction Model**  
   Predicts crowding level at stops/stations/vehicles using tap-in count, headway, capacity, time, weather, and event indicators.

3. **Personalized Walking Time Estimation**  
   Uses walking-time categories in the prototype and can personalize transfer time with user consent using walking profile multipliers.

4. **Missed-Connection Risk Scoring**  
   Converts ETA, walking time, fixed rail schedule, density, and model confidence into a risk score.

5. **Rail-Fixed Intermodal Optimizer**  
   Makes operational recommendations while keeping rail schedules unchanged.

## Strategy sentence

Our strategy treats rail-based transport as a fixed schedule anchor and optimizes flexible non-rail modes around it using AI-based ETA prediction, passenger density forecasting, personalized walking-time estimation, missed-connection risk scoring, and constraint-based intermodal recommendation.
