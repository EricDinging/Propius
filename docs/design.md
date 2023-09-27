# Design


## API
1. Job provide total round estimation
    - Estimate total demand as current demand times total round
    - Remove job after reaching total round
2. Job does not provide total round estimation
    - Estimate total demand as twice of the total demand
    - Remove job after 100 rounds