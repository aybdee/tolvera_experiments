# tolvera-experiments
Simple vera implementation experiments

### Attract
Each particle is attracted to the center of mass of its own species and also experiences an attractive or repulsive force toward the center of mass of every other species. The cross-species force is scaled down by about half so that the attraction to its own center of mass remains dominant. (Quite similar to particle life)

![image](https://github.com/user-attachments/assets/ebe6173b-315b-4c41-966a-3f5a2cef64cd)

#### Ant Colony
The Ants move through a 2D space, searching for food and returning it to their nest while depositing pheromones.
- **Pheromone Trails**: Two types—food and nest pheromones—guide ants based on intensity and direction.
- **Food & Nest Detection**: Ants detect food and nest proximity to switch behaviors.
- **Ant Movement**:  
  - Random exploration or pheromone-guided movement.  
  - When an ant finds food, it reverses direction toward the nest.  
  - Upon reaching the nest, it drops the food and resumes searching.  
- **Pheromone Deposition & Decay**: Ants leave pheromones along their path, which gradually decay over time.

still a work in progress
![image](https://github.com/user-attachments/assets/64dc82fc-7c24-42f7-a1f1-911ede78b407) 
